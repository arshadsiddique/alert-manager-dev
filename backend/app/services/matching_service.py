import re
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from ..core.config import settings

# Optional: Try to import sklearn, fallback to basic similarity if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("sklearn not available, using basic text similarity")

logger = logging.getLogger(__name__)

class AlertMatchingService:
    """Enhanced alert matching service with multiple similarity algorithms"""
    
    def __init__(self, confidence_threshold: float = None):
        self.confidence_threshold = confidence_threshold or settings.ALERT_MATCH_CONFIDENCE_THRESHOLD / 100.0
        self.high_confidence_threshold = getattr(settings, 'ALERT_MATCH_HIGH_CONFIDENCE_THRESHOLD', 85.0) / 100.0
        self.manual_review_threshold = getattr(settings, 'ALERT_MATCH_MANUAL_REVIEW_THRESHOLD', 60.0) / 100.0
        self.time_window_minutes = getattr(settings, 'ALERT_MATCH_TIME_WINDOW_MINUTES', 15)
        
        # Initialize text vectorizer if sklearn is available
        if SKLEARN_AVAILABLE:
            try:
                self.vectorizer = TfidfVectorizer(
                    stop_words='english',
                    ngram_range=(1, 2),
                    max_features=1000,
                    lowercase=True,
                    token_pattern=r'\b[a-zA-Z0-9\-_]{2,}\b'  # Include hyphenated words
                )
            except Exception as e:
                logger.warning(f"Failed to initialize TfidfVectorizer: {e}")
                self.vectorizer = None
        else:
            self.vectorizer = None
        
        # Matching weights for different components
        self.weights = {
            'name_similarity': 0.40,      # Alert name matching is most important
            'cluster_similarity': 0.25,   # Cluster/instance matching
            'severity_similarity': 0.15,  # Severity level matching
            'temporal_similarity': 0.10,  # Time proximity
            'content_similarity': 0.10    # Content/description similarity
        }
        
        logger.info(f"AlertMatchingService initialized with threshold: {self.confidence_threshold:.2%}")
    
    def match_grafana_with_jsm(self, grafana_alerts: List[Dict], jsm_alerts: List[Dict]) -> List[Dict]:
        """
        Match Grafana alerts with JSM alerts using enhanced algorithm.
        
        Returns list of match results with confidence scores.
        """
        start_time = time.time()
        matches = []
        used_jsm_alerts = set()
        
        logger.info(f"Starting alert matching: {len(grafana_alerts)} Grafana alerts, {len(jsm_alerts)} JSM alerts")
        
        for i, grafana_alert in enumerate(grafana_alerts):
            match_info = {
                'grafana_alert': grafana_alert,
                'jsm_alert': None,
                'match_type': 'none',
                'match_confidence': 0.0,
                'match_details': {}
            }
            
            best_match = None
            best_confidence = 0.0
            best_details = {}
            
            # Try to match with each available JSM alert
            for jsm_alert in jsm_alerts:
                jsm_id = self._safe_str(jsm_alert.get('id', ''))
                if jsm_id in used_jsm_alerts:
                    continue
                
                try:
                    confidence, details = self.calculate_match_confidence(grafana_alert, jsm_alert)
                    
                    if confidence > best_confidence and confidence >= self.confidence_threshold:
                        best_confidence = confidence
                        best_match = jsm_alert
                        best_details = details
                        
                except Exception as e:
                    logger.error(f"Error matching alerts: {e}")
                    continue
            
            # If we found a good match, use it
            if best_match:
                match_info['jsm_alert'] = best_match
                match_info['match_confidence'] = best_confidence
                match_info['match_details'] = best_details
                match_info['match_type'] = self._determine_match_type(best_confidence, best_details)
                
                best_match_id = self._safe_str(best_match.get('id', ''))
                used_jsm_alerts.add(best_match_id)
                
                if getattr(settings, 'LOG_MATCHING_DETAILS', True):
                    grafana_name = self._extract_grafana_alert_name(grafana_alert)
                    jsm_tiny_id = self._safe_str(best_match.get('tinyId', best_match.get('id', 'unknown')))
                    logger.info(f"✅ Matched '{grafana_name}' with JSM #{jsm_tiny_id} (confidence: {best_confidence:.1%})")
            
            matches.append(match_info)
            
            # Log progress for large batches
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(grafana_alerts)} alerts")
        
        processing_time = time.time() - start_time
        matches_found = len([m for m in matches if m['jsm_alert'] is not None])
        
        logger.info(f"Alert matching completed in {processing_time:.2f}s: {matches_found}/{len(matches)} alerts matched")
        
        return matches
    
    def calculate_match_confidence(self, grafana_alert: Dict, jsm_alert: Dict) -> Tuple[float, Dict]:
        """
        Calculate comprehensive match confidence between Grafana and JSM alerts.
        
        Returns:
            Tuple of (confidence_score, details_dict)
        """
        try:
            scores = {}
            details = {}
            
            # 1. Alert Name Similarity (40% weight)
            grafana_name = self._extract_grafana_alert_name(grafana_alert)
            jsm_name = self._extract_jsm_alert_name(jsm_alert)
            
            if grafana_name and jsm_name:
                name_score, name_details = self._calculate_name_similarity(grafana_name, jsm_name)
                scores['name_similarity'] = name_score
                details['name_match'] = name_details
            else:
                scores['name_similarity'] = 0.0
                details['name_match'] = {'reason': 'missing_names', 'grafana_name': grafana_name, 'jsm_name': jsm_name}
            
            # 2. Cluster/Instance Similarity (25% weight)
            grafana_cluster = self._extract_grafana_cluster(grafana_alert)
            jsm_cluster = self._extract_jsm_cluster(jsm_alert)
            
            cluster_score, cluster_details = self._calculate_cluster_similarity(grafana_cluster, jsm_cluster)
            scores['cluster_similarity'] = cluster_score
            details['cluster_match'] = cluster_details
            
            # 3. Severity Similarity (15% weight)
            grafana_severity = self._extract_grafana_severity(grafana_alert)
            jsm_severity = self._extract_jsm_severity(jsm_alert)
            
            severity_score, severity_details = self._calculate_severity_similarity(grafana_severity, jsm_severity)
            scores['severity_similarity'] = severity_score
            details['severity_match'] = severity_details
            
            # 4. Temporal Proximity (10% weight)
            temporal_score, temporal_details = self._calculate_temporal_similarity(grafana_alert, jsm_alert)
            scores['temporal_similarity'] = temporal_score
            details['temporal_match'] = temporal_details
            
            # 5. Content Similarity (10% weight)
            content_score, content_details = self._calculate_content_similarity(grafana_alert, jsm_alert)
            scores['content_similarity'] = content_score
            details['content_match'] = content_details
            
            # Calculate weighted confidence score
            confidence = sum(scores[key] * self.weights[key] for key in scores.keys())
            
            # Add component scores to details
            details['component_scores'] = scores
            details['final_confidence'] = confidence
            
            # Log detailed scoring for debugging if enabled
            if getattr(settings, 'DEBUG_MATCHING_ENABLED', False):
                logger.debug(f"Match confidence details: {scores}, Final: {confidence:.2%}")
            
            return confidence, details
            
        except Exception as e:
            logger.error(f"Error calculating match confidence: {e}")
            return 0.0, {'error': str(e)}
    
    def _calculate_name_similarity(self, grafana_name: str, jsm_name: str) -> Tuple[float, Dict]:
        """Calculate similarity between alert names using multiple methods."""
        if not grafana_name or not jsm_name:
            return 0.0, {'method': 'missing_names'}
        
        # Normalize names for comparison
        grafana_norm = self._normalize_alert_name(grafana_name)
        jsm_norm = self._normalize_alert_name(jsm_name)
        
        # Exact match
        if grafana_norm == jsm_norm:
            return 1.0, {'method': 'exact_match', 'normalized_names': [grafana_norm, jsm_norm]}
        
        # Substring matching
        if grafana_norm in jsm_norm or jsm_norm in grafana_norm:
            return 0.90, {'method': 'substring_match', 'normalized_names': [grafana_norm, jsm_norm]}
        
        # Sequence matching (handles typos and variations)
        sequence_ratio = SequenceMatcher(None, grafana_norm, jsm_norm).ratio()
        
        # Word-based Jaccard similarity
        grafana_words = set(grafana_norm.split())
        jsm_words = set(jsm_norm.split())
        
        jaccard_ratio = 0.0
        if grafana_words and jsm_words:
            intersection = grafana_words.intersection(jsm_words)
            union = grafana_words.union(jsm_words)
            jaccard_ratio = len(intersection) / len(union) if union else 0
        
        # Take the maximum of the similarity measures
        max_ratio = max(sequence_ratio, jaccard_ratio)
        
        method = 'sequence_match' if sequence_ratio > jaccard_ratio else 'jaccard_similarity'
        
        return max_ratio, {
            'method': method,
            'sequence_ratio': sequence_ratio,
            'jaccard_ratio': jaccard_ratio,
            'normalized_names': [grafana_norm, jsm_norm],
            'word_overlap': len(grafana_words.intersection(jsm_words)) if grafana_words and jsm_words else 0
        }
    
    def _calculate_cluster_similarity(self, grafana_cluster: str, jsm_cluster: str) -> Tuple[float, Dict]:
        """Calculate cluster/instance similarity."""
        if not jsm_cluster:
            return 0.5, {'method': 'no_jsm_cluster', 'reason': 'neutral_score'}
        
        if not grafana_cluster:
            return 0.3, {'method': 'no_grafana_cluster', 'reason': 'low_score'}
        
        # Exact match
        if grafana_cluster.lower() == jsm_cluster.lower():
            return 1.0, {'method': 'exact_match', 'clusters': [grafana_cluster, jsm_cluster]}
        
        # Substring matching
        grafana_lower = grafana_cluster.lower()
        jsm_lower = jsm_cluster.lower()
        
        if grafana_lower in jsm_lower or jsm_lower in grafana_lower:
            return 0.85, {'method': 'substring_match', 'clusters': [grafana_cluster, jsm_cluster]}
        
        # Sequence similarity
        similarity = SequenceMatcher(None, grafana_lower, jsm_lower).ratio()
        
        return similarity, {
            'method': 'sequence_similarity',
            'similarity_ratio': similarity,
            'clusters': [grafana_cluster, jsm_cluster]
        }
    
    def _calculate_severity_similarity(self, grafana_severity: str, jsm_severity: str) -> Tuple[float, Dict]:
        """Calculate severity similarity with mapping."""
        # Severity mapping groups
        severity_groups = {
            'critical': ['critical', 'crit', 'p1', 'high'],
            'warning': ['warning', 'warn', 'p2', 'medium'],
            'info': ['info', 'information', 'p3', 'p5', 'low'],
            'low': ['low', 'minor', 'p4']
        }
        
        # Normalize severities
        grafana_norm = grafana_severity.lower() if grafana_severity else 'info'
        jsm_norm = jsm_severity.lower() if jsm_severity else 'info'
        
        # Direct match
        if grafana_norm == jsm_norm:
            return 1.0, {'method': 'exact_match', 'severities': [grafana_severity, jsm_severity]}
        
        # Find which groups they belong to
        grafana_group = None
        jsm_group = None
        
        for group, keywords in severity_groups.items():
            if grafana_norm in keywords:
                grafana_group = group
            if jsm_norm in keywords:
                jsm_group = group
        
        if grafana_group and jsm_group:
            if grafana_group == jsm_group:
                return 1.0, {
                    'method': 'group_match',
                    'severities': [grafana_severity, jsm_severity],
                    'group': grafana_group
                }
            else:
                return 0.3, {
                    'method': 'different_groups',
                    'severities': [grafana_severity, jsm_severity],
                    'groups': [grafana_group, jsm_group]
                }
        
        return 0.5, {
            'method': 'unknown_mapping',
            'severities': [grafana_severity, jsm_severity],
            'reason': 'could_not_categorize'
        }
    
    def _calculate_temporal_similarity(self, grafana_alert: Dict, jsm_alert: Dict) -> Tuple[float, Dict]:
        """Calculate temporal proximity similarity."""
        try:
            # Parse timestamps
            grafana_time = self._parse_grafana_timestamp(grafana_alert)
            jsm_time = self._parse_jsm_timestamp(jsm_alert)
            
            if not grafana_time or not jsm_time:
                return 0.5, {
                    'method': 'missing_timestamps',
                    'grafana_time': str(grafana_time) if grafana_time else None,
                    'jsm_time': str(jsm_time) if jsm_time else None
                }
            
            # Calculate time difference in minutes
            time_diff = abs((grafana_time - jsm_time).total_seconds()) / 60
            
            # Score based on time window
            if time_diff <= 2:
                score = 1.0
                category = 'very_close'
            elif time_diff <= 5:
                score = 0.9
                category = 'close'
            elif time_diff <= 15:
                score = 0.7
                category = 'within_window'
            elif time_diff <= 30:
                score = 0.5
                category = 'nearby'
            elif time_diff <= 60:
                score = 0.3
                category = 'distant'
            else:
                score = 0.1
                category = 'very_distant'
            
            return score, {
                'method': 'time_proximity',
                'time_diff_minutes': time_diff,
                'category': category,
                'grafana_time': grafana_time.isoformat(),
                'jsm_time': jsm_time.isoformat()
            }
                
        except Exception as e:
            logger.error(f"Error calculating temporal similarity: {e}")
            return 0.5, {'method': 'error', 'error': str(e)}
    
    def _calculate_content_similarity(self, grafana_alert: Dict, jsm_alert: Dict) -> Tuple[float, Dict]:
        """Calculate content similarity using available methods."""
        try:
            # Extract text content
            grafana_text = self._extract_grafana_text(grafana_alert)
            jsm_text = self._extract_jsm_text(jsm_alert)
            
            if not grafana_text or not jsm_text:
                return 0.5, {
                    'method': 'missing_content',
                    'grafana_length': len(grafana_text) if grafana_text else 0,
                    'jsm_length': len(jsm_text) if jsm_text else 0
                }
            
            # Use TF-IDF if available, otherwise use basic similarity
            if self.vectorizer and SKLEARN_AVAILABLE:
                try:
                    texts = [grafana_text, jsm_text]
                    tfidf_matrix = self.vectorizer.fit_transform(texts)
                    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                    
                    return similarity, {
                        'method': 'tfidf_cosine',
                        'similarity': similarity,
                        'text_lengths': [len(grafana_text), len(jsm_text)]
                    }
                except Exception as e:
                    logger.warning(f"TF-IDF similarity failed, using basic method: {e}")
            
            # Fallback to basic word overlap similarity
            grafana_words = set(re.findall(r'\b\w+\b', grafana_text.lower()))
            jsm_words = set(re.findall(r'\b\w+\b', jsm_text.lower()))
            
            if grafana_words and jsm_words:
                intersection = grafana_words.intersection(jsm_words)
                union = grafana_words.union(jsm_words)
                similarity = len(intersection) / len(union)
                
                return similarity, {
                    'method': 'word_overlap',
                    'similarity': similarity,
                    'common_words': len(intersection),
                    'total_words': len(union),
                    'text_lengths': [len(grafana_text), len(jsm_text)]
                }
            
            return 0.3, {
                'method': 'no_words_found',
                'reason': 'could_not_extract_words'
            }
            
        except Exception as e:
            logger.error(f"Error calculating content similarity: {e}")
            return 0.5, {'method': 'error', 'error': str(e)}
    
    def _determine_match_type(self, confidence: float, details: Dict) -> str:
        """Determine match type based on confidence and details."""
        if confidence >= self.high_confidence_threshold:
            return 'high_confidence'
        elif confidence >= self.confidence_threshold:
            if details.get('name_match', {}).get('method') == 'exact_match':
                return 'exact_name_match'
            elif details.get('cluster_match', {}).get('method') == 'exact_match':
                return 'cluster_match'
            else:
                return 'content_similarity'
        elif confidence >= self.manual_review_threshold:
            return 'manual_review'
        else:
            return 'low_confidence'
    
    # Helper methods for data extraction
    def _extract_grafana_alert_name(self, alert: Dict) -> str:
        """Extract alert name from Grafana alert."""
        return alert.get('labels', {}).get('alertname', '') or alert.get('alert_name', '')
    
    def _extract_grafana_cluster(self, alert: Dict) -> str:
        """Extract cluster from Grafana alert."""
        labels = alert.get('labels', {})
        return labels.get('cluster', '') or labels.get('instance', '')
    
    def _extract_grafana_severity(self, alert: Dict) -> str:
        """Extract severity from Grafana alert."""
        return alert.get('labels', {}).get('severity', 'info')
    
    def _extract_jsm_alert_name(self, alert: Dict) -> str:
        """Extract alert name from JSM alert."""
        from .jsm_service import JSMService
        jsm_service = JSMService()
        return jsm_service.extract_alert_name_from_jsm(alert) or ''
    
    def _extract_jsm_cluster(self, alert: Dict) -> str:
        """Extract cluster from JSM alert."""
        from .jsm_service import JSMService
        jsm_service = JSMService()
        return jsm_service.extract_cluster_from_jsm(alert) or ''
    
    def _extract_jsm_severity(self, alert: Dict) -> str:
        """Extract severity from JSM alert."""
        from .jsm_service import JSMService
        jsm_service = JSMService()
        return jsm_service.extract_severity_from_jsm(alert) or 'info'
    
    def _normalize_alert_name(self, name: str) -> str:
        """Normalize alert name for comparison."""
        if not name:
            return ''
        
        # Remove special characters and convert to lowercase
        normalized = re.sub(r'[^\w\s-]', '', name.lower())
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(alert|rule|notification)[:\s]*', '', normalized)
        normalized = re.sub(r'[:\s]*(alert|rule|notification)$', '', normalized)
        
        return normalized
    
    def _extract_grafana_text(self, alert: Dict) -> str:
        """Extract searchable text from Grafana alert."""
        text_parts = []
        
        # Add alert name
        labels = alert.get('labels', {})
        if 'alertname' in labels:
            text_parts.append(labels['alertname'])
        
        # Add annotations
        annotations = alert.get('annotations', {})
        for key, value in annotations.items():
            if isinstance(value, str) and value.strip():
                text_parts.append(value)
        
        # Add summary if available
        if 'summary' in alert:
            text_parts.append(str(alert['summary']))
        
        return ' '.join(text_parts)
    
    def _extract_jsm_text(self, alert: Dict) -> str:
        """Extract searchable text from JSM alert."""
        alert_data = alert.get('data', alert)
        text_parts = []
        
        # Add message
        message = alert_data.get('message', '')
        if message:
            text_parts.append(message)
        
        # Add description
        description = alert_data.get('description', '')
        if description:
            text_parts.append(description)
        
        # Add relevant tags (filter out noisy ones)
        tags = alert_data.get('tags', [])
        relevant_tags = []
        for tag in tags:
            if isinstance(tag, str) and not any(exclude in tag.lower() for exclude in ['ip:', 'id:', 'uuid:']):
                relevant_tags.append(tag)
        
        if relevant_tags:
            text_parts.extend(relevant_tags)
        
        return ' '.join(str(part) for part in text_parts if part)
    
    def _parse_grafana_timestamp(self, alert: Dict) -> Optional[datetime]:
        """Parse timestamp from Grafana alert."""
        timestamp_str = alert.get('startsAt') or alert.get('started_at')
        if not timestamp_str:
            return None
        
        try:
            if isinstance(timestamp_str, str):
                # Handle ISO format with Z suffix
                if timestamp_str.endswith('Z'):
                    timestamp_str = timestamp_str[:-1] + '+00:00'
                return datetime.fromisoformat(timestamp_str)
            elif isinstance(timestamp_str, datetime):
                return timestamp_str
        except Exception as e:
            logger.warning(f"Failed to parse Grafana timestamp '{timestamp_str}': {e}")
        
        return None
    
    def _parse_jsm_timestamp(self, alert: Dict) -> Optional[datetime]:
        """Parse timestamp from JSM alert."""
        alert_data = alert.get('data', alert)
        timestamp_str = alert_data.get('createdAt') or alert_data.get('jsm_created_at')
        
        if not timestamp_str:
            return None
        
        try:
            if isinstance(timestamp_str, str):
                # Handle ISO format with Z suffix
                if timestamp_str.endswith('Z'):
                    timestamp_str = timestamp_str[:-1] + '+00:00'
                return datetime.fromisoformat(timestamp_str)
            elif isinstance(timestamp_str, datetime):
                return timestamp_str
        except Exception as e:
            logger.warning(f"Failed to parse JSM timestamp '{timestamp_str}': {e}")
        
        return None
    
    def _safe_str(self, value: Any) -> str:
        """Safely convert any value to string."""
        if value is None:
            return ""
        return str(value)