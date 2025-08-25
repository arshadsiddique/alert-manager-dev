import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum

logger = logging.getLogger(__name__)

class MatchType(Enum):
    """Enumeration of different match types."""
    EXACT_MATCH = "exact_match"
    HIGH_CONFIDENCE = "high_confidence"
    CONTENT_SIMILARITY = "content_similarity"
    CLUSTER_MATCH = "cluster_match"
    MANUAL_REVIEW = "manual_review"
    LOW_CONFIDENCE = "low_confidence"
    NO_MATCH = "no_match"

@dataclass
class MatchingAttempt:
    """Record of a single matching attempt."""
    timestamp: datetime
    grafana_alert_name: str
    jsm_alert_id: Optional[str]
    confidence_score: float
    match_type: MatchType
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None
    match_details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MatchingMetrics:
    """Comprehensive matching metrics collection."""
    
    # Basic counters
    total_attempts: int = 0
    successful_matches: int = 0
    high_confidence_matches: int = 0
    manual_review_required: int = 0
    failed_matches: int = 0
    
    # Processing times
    processing_times: List[float] = field(default_factory=list)
    
    # Confidence distribution
    confidence_scores: List[float] = field(default_factory=list)
    
    # Match type distribution
    match_type_counts: Dict[MatchType, int] = field(default_factory=lambda: defaultdict(int))
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    
    # Timing information
    start_time: datetime = field(default_factory=datetime.utcnow)
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    # Detailed attempts (optional, for debugging)
    detailed_attempts: List[MatchingAttempt] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.processing_times:
            self.processing_times = []
        if not self.confidence_scores:
            self.confidence_scores = []
    
    def record_attempt(self, attempt: MatchingAttempt):
        """Record a matching attempt."""
        self.total_attempts += 1
        self.last_update = datetime.utcnow()
        
        if attempt.success:
            self.successful_matches += 1
            self.confidence_scores.append(attempt.confidence_score)
            
            if attempt.confidence_score >= 0.85:
                self.high_confidence_matches += 1
            elif attempt.match_type == MatchType.MANUAL_REVIEW:
                self.manual_review_required += 1
        else:
            self.failed_matches += 1
            if attempt.error_message:
                self.errors.append(attempt.error_message)
        
        self.processing_times.append(attempt.processing_time_ms)
        self.match_type_counts[attempt.match_type] += 1
        
        # Store detailed attempt if tracking is enabled
        if len(self.detailed_attempts) < 1000:  # Limit to prevent memory issues
            self.detailed_attempts.append(attempt)
    
    def get_match_rate(self) -> float:
        """Get overall match rate."""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_matches / self.total_attempts
    
    def get_high_confidence_rate(self) -> float:
        """Get high confidence match rate."""
        if self.successful_matches == 0:
            return 0.0
        return self.high_confidence_matches / self.successful_matches
    
    def get_average_processing_time(self) -> float:
        """Get average processing time in milliseconds."""
        if not self.processing_times:
            return 0.0
        return sum(self.processing_times) / len(self.processing_times)
    
    def get_average_confidence(self) -> float:
        """Get average confidence score."""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)
    
    def get_confidence_distribution(self) -> Dict[str, int]:
        """Get confidence score distribution."""
        if not self.confidence_scores:
            return {}
        
        buckets = {
            '90-100%': 0,
            '80-89%': 0,
            '70-79%': 0,
            '60-69%': 0,
            '50-59%': 0,
            'Below 50%': 0
        }
        
        for score in self.confidence_scores:
            percentage = score * 100
            if percentage >= 90:
                buckets['90-100%'] += 1
            elif percentage >= 80:
                buckets['80-89%'] += 1
            elif percentage >= 70:
                buckets['70-79%'] += 1
            elif percentage >= 60:
                buckets['60-69%'] += 1
            elif percentage >= 50:
                buckets['50-59%'] += 1
            else:
                buckets['Below 50%'] += 1
        
        return buckets
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        duration = (self.last_update - self.start_time).total_seconds()
        
        return {
            'overview': {
                'total_attempts': self.total_attempts,
                'successful_matches': self.successful_matches,
                'match_rate': round(self.get_match_rate() * 100, 2),
                'high_confidence_matches': self.high_confidence_matches,
                'high_confidence_rate': round(self.get_high_confidence_rate() * 100, 2),
                'manual_review_required': self.manual_review_required,
                'failed_matches': self.failed_matches,
                'error_count': len(self.errors)
            },
            'performance': {
                'average_processing_time_ms': round(self.get_average_processing_time(), 2),
                'total_processing_time_ms': round(sum(self.processing_times), 2),
                'min_processing_time_ms': round(min(self.processing_times), 2) if self.processing_times else 0,
                'max_processing_time_ms': round(max(self.processing_times), 2) if self.processing_times else 0,
                'total_duration_seconds': round(duration, 2)
            },
            'confidence': {
                'average_confidence': round(self.get_average_confidence() * 100, 2),
                'confidence_distribution': self.get_confidence_distribution()
            },
            'match_types': {
                match_type.value: count 
                for match_type, count in self.match_type_counts.items()
            },
            'timing': {
                'start_time': self.start_time.isoformat(),
                'last_update': self.last_update.isoformat(),
                'duration_seconds': round(duration, 2)
            }
        }

class MetricsCollector:
    """Centralized metrics collection for alert matching."""
    
    def __init__(self):
        self.session_metrics = MatchingMetrics()
        self.historical_metrics = []
        self.alert_specific_metrics = defaultdict(list)
        
    def start_matching_session(self):
        """Start a new matching session."""
        if self.session_metrics.total_attempts > 0:
            # Save current session to history
            self.historical_metrics.append(self.session_metrics)
            
            # Keep only last 10 sessions to prevent memory bloat
            if len(self.historical_metrics) > 10:
                self.historical_metrics = self.historical_metrics[-10:]
        
        # Start new session
        self.session_metrics = MatchingMetrics()
        logger.info("Started new matching metrics session")
    
    def record_match_attempt(
        self,
        grafana_alert_name: str,
        jsm_alert_id: Optional[str],
        confidence_score: float,
        match_type: str,
        processing_time_ms: float,
        success: bool,
        error_message: Optional[str] = None,
        match_details: Optional[Dict] = None
    ):
        """Record a single matching attempt."""
        
        # Convert string match type to enum
        try:
            match_type_enum = MatchType(match_type)
        except ValueError:
            match_type_enum = MatchType.NO_MATCH
        
        attempt = MatchingAttempt(
            timestamp=datetime.utcnow(),
            grafana_alert_name=grafana_alert_name,
            jsm_alert_id=jsm_alert_id,
            confidence_score=confidence_score,
            match_type=match_type_enum,
            processing_time_ms=processing_time_ms,
            success=success,
            error_message=error_message,
            match_details=match_details or {}
        )
        
        # Record in session metrics
        self.session_metrics.record_attempt(attempt)
        
        # Record alert-specific metrics
        self.alert_specific_metrics[grafana_alert_name].append(attempt)
        
        # Log significant events
        if success and confidence_score >= 0.85:
            logger.debug(f"High confidence match: {grafana_alert_name} -> {jsm_alert_id} ({confidence_score:.2%})")
        elif not success:
            logger.warning(f"Failed match attempt: {grafana_alert_name} - {error_message}")
    
    def get_current_session_metrics(self) -> Dict[str, Any]:
        """Get current session metrics."""
        return self.session_metrics.get_summary()
    
    def get_historical_summary(self) -> Dict[str, Any]:
        """Get summary of historical metrics."""
        if not self.historical_metrics:
            return {'message': 'No historical data available'}
        
        total_attempts = sum(m.total_attempts for m in self.historical_metrics)
        total_successes = sum(m.successful_matches for m in self.historical_metrics)
        total_high_confidence = sum(m.high_confidence_matches for m in self.historical_metrics)
        
        avg_processing_time = sum(m.get_average_processing_time() for m in self.historical_metrics) / len(self.historical_metrics)
        avg_confidence = sum(m.get_average_confidence() for m in self.historical_metrics) / len(self.historical_metrics)
        
        return {
            'sessions_count': len(self.historical_metrics),
            'total_attempts': total_attempts,
            'total_successes': total_successes,
            'overall_match_rate': round((total_successes / total_attempts * 100) if total_attempts > 0 else 0, 2),
            'total_high_confidence': total_high_confidence,
            'high_confidence_rate': round((total_high_confidence / total_successes * 100) if total_successes > 0 else 0, 2),
            'average_processing_time_ms': round(avg_processing_time, 2),
            'average_confidence': round(avg_confidence * 100, 2)
        }
    
    def get_alert_specific_metrics(self, alert_name: str) -> Dict[str, Any]:
        """Get metrics for a specific alert name."""
        attempts = self.alert_specific_metrics.get(alert_name, [])
        
        if not attempts:
            return {'message': f'No data for alert: {alert_name}'}
        
        successful_attempts = [a for a in attempts if a.success]
        confidence_scores = [a.confidence_score for a in successful_attempts]
        
        return {
            'alert_name': alert_name,
            'total_attempts': len(attempts),
            'successful_matches': len(successful_attempts),
            'match_rate': round((len(successful_attempts) / len(attempts) * 100) if attempts else 0, 2),
            'average_confidence': round((sum(confidence_scores) / len(confidence_scores) * 100) if confidence_scores else 0, 2),
            'best_confidence': round(max(confidence_scores) * 100, 2) if confidence_scores else 0,
            'match_types': dict(Counter(a.match_type.value for a in attempts)),
            'last_attempt': attempts[-1].timestamp.isoformat() if attempts else None
        }
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights and recommendations."""
        current = self.session_metrics
        insights = []
        
        # Match rate insights
        match_rate = current.get_match_rate()
        if match_rate < 0.5:
            insights.append({
                'type': 'warning',
                'message': f'Low match rate ({match_rate:.1%}). Consider lowering confidence threshold.',
                'metric': 'match_rate',
                'value': match_rate
            })
        elif match_rate > 0.9:
            insights.append({
                'type': 'success',
                'message': f'Excellent match rate ({match_rate:.1%}).',
                'metric': 'match_rate',
                'value': match_rate
            })
        
        # Processing time insights
        avg_time = current.get_average_processing_time()
        if avg_time > 1000:  # More than 1 second
            insights.append({
                'type': 'warning',
                'message': f'High average processing time ({avg_time:.0f}ms). Consider optimization.',
                'metric': 'processing_time',
                'value': avg_time
            })
        
        # Confidence insights
        avg_confidence = current.get_average_confidence()
        if avg_confidence < 0.7:
            insights.append({
                'type': 'info',
                'message': f'Low average confidence ({avg_confidence:.1%}). Review matching algorithms.',
                'metric': 'confidence',
                'value': avg_confidence
            })
        
        # Manual review insights
        manual_review_rate = current.manual_review_required / current.total_attempts if current.total_attempts > 0 else 0
        if manual_review_rate > 0.2:
            insights.append({
                'type': 'info',
                'message': f'High manual review rate ({manual_review_rate:.1%}). Consider tuning thresholds.',
                'metric': 'manual_review_rate',
                'value': manual_review_rate
            })
        
        return {
            'insights': insights,
            'recommendations': self._generate_recommendations(current),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def _generate_recommendations(self, metrics: MatchingMetrics) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        match_rate = metrics.get_match_rate()
        avg_confidence = metrics.get_average_confidence()
        
        if match_rate < 0.3:
            recommendations.append("Consider significantly lowering the confidence threshold")
            recommendations.append("Review JSM alert data extraction logic")
            recommendations.append("Check if JSM alerts contain expected fields")
        
        if match_rate < 0.6 and avg_confidence > 0.8:
            recommendations.append("Confidence threshold may be too high - consider lowering it")
        
        if avg_confidence < 0.5:
            recommendations.append("Review alert name extraction algorithms")
            recommendations.append("Improve text similarity calculations")
            recommendations.append("Check for data quality issues in source systems")
        
        if metrics.get_average_processing_time() > 500:
            recommendations.append("Optimize matching algorithms for better performance")
            recommendations.append("Consider caching frequently accessed data")
        
        manual_review_rate = metrics.manual_review_required / metrics.total_attempts if metrics.total_attempts > 0 else 0
        if manual_review_rate > 0.3:
            recommendations.append("Implement machine learning for better automatic matching")
            recommendations.append("Create more specific matching rules for common patterns")
        
        return recommendations
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external analysis."""
        return {
            'current_session': self.get_current_session_metrics(),
            'historical_summary': self.get_historical_summary(),
            'performance_insights': self.get_performance_insights(),
            'export_timestamp': datetime.utcnow().isoformat()
        }
    
    def log_summary(self):
        """Log a summary of current metrics."""
        summary = self.get_current_session_metrics()
        overview = summary['overview']
        performance = summary['performance']
        
        logger.info(
            f"Matching Session Summary: {overview['successful_matches']}/{overview['total_attempts']} matches "
            f"({overview['match_rate']}% success rate, {overview['high_confidence_rate']}% high confidence, "
            f"avg {performance['average_processing_time_ms']}ms processing time)"
        )
        
        if overview['error_count'] > 0:
            logger.warning(f"Session had {overview['error_count']} errors")

# Global metrics collector instance
metrics_collector = MetricsCollector()