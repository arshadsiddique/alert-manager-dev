import requests
import logging
import base64
import hashlib
import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.config import settings

logger = logging.getLogger(__name__)

class JSMService:
    def __init__(self):
        self.base_url = "https://api.atlassian.com/jsm/ops/api"
        self.tenant_url = settings.JIRA_URL  # e.g., https://devoinc.atlassian.net
        self.user_email = settings.JIRA_USER_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.cloud_id = settings.JSM_CLOUD_ID
        
        # Create basic auth header
        auth_string = f"{self.user_email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 60 / getattr(settings, 'JSM_RATE_LIMIT_PER_MINUTE', 500)
    
    def _rate_limit(self):
        """Implement rate limiting for JSM API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _safe_str(self, value: Any) -> str:
        """Safely convert any value to string, handling None values"""
        if value is None:
            return ""
        return str(value)
    
    def _safe_lower(self, value: Any) -> str:
        """Safely convert any value to lowercase string, handling None values"""
        if value is None:
            return ""
        return str(value).lower()
    
    async def get_cloud_id(self) -> Optional[str]:
        """Retrieve Atlassian Cloud ID from tenant info"""
        if self.cloud_id:
            return self.cloud_id
            
        try:
            self._rate_limit()
            url = f"{self.tenant_url}/_edge/tenant_info"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.cloud_id = data.get('cloudId')
            
            if self.cloud_id:
                logger.info(f"Retrieved Cloud ID: {self.cloud_id}")
                return self.cloud_id
            else:
                logger.error("Cloud ID not found in tenant info")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error retrieving Cloud ID: {e}")
            return None
    
    async def get_jsm_alerts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch alerts from JSM with enhanced error handling"""
        try:
            cloud_id = await self.get_cloud_id()
            if not cloud_id:
                logger.error("Cannot fetch JSM alerts without Cloud ID")
                return []
            
            self._rate_limit()
            url = f"{self.base_url}/{cloud_id}/v1/alerts"
            params = {
                "limit": min(limit, 100),  # JSM API limit
                "offset": offset,
                "sort": "createdAt",
                "order": "desc"
            }
            
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params,
                timeout=getattr(settings, 'JSM_API_TIMEOUT', 30)
            )
            response.raise_for_status()
            
            data = response.json()
            alerts = data.get('values', [])
            
            logger.info(f"Retrieved {len(alerts)} JSM alerts from API")
            
            # Log sample alert for debugging if enabled
            if alerts and getattr(settings, 'DEBUG_MATCHING_ENABLED', False):
                sample_alert = alerts[0]
                logger.debug(f"Sample JSM alert: {sample_alert}")
            
            return alerts
            
        except requests.RequestException as e:
            logger.error(f"Error fetching JSM alerts: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return []
    
    def extract_alert_name_from_jsm(self, jsm_alert: Dict[str, Any]) -> Optional[str]:
        """
        Extract alert name from JSM alert with multiple fallback strategies.
        
        Priority order:
        1. Tags with 'alertname:' prefix
        2. Parse from message field 
        3. Use alias field
        4. Extract from description using patterns
        """
        try:
            # Handle nested data structure if present
            alert_data = jsm_alert.get('data', jsm_alert)
            
            # Strategy 1: Check tags for alertname prefix
            tags = alert_data.get('tags', [])
            for tag in tags:
                if isinstance(tag, str) and tag.startswith('alertname:'):
                    alert_name = tag.split(':', 1)[1].strip()
                    if alert_name and self._is_valid_alert_name(alert_name):
                        logger.debug(f"Extracted alert name from tag: {alert_name}")
                        return alert_name
            
            # Strategy 2: Parse from message field
            message = self._safe_str(alert_data.get('message', '')).strip()
            if message:
                # Look for Grafana-style message format
                # Pattern: [Grafana]: *Summary*: AlertName
                grafana_patterns = [
                    r'\[Grafana\]:\s*\*[^*]+\*:\s*([^\s\n]+)',
                    r'\*Summary\*:\s*([^\s\n*]+)',
                    r'Alert:\s*([A-Za-z0-9\-_]+)',
                    r'^([A-Za-z0-9\-_]{3,})',  # Start of message if it looks like alert name
                ]
                
                for pattern in grafana_patterns:
                    match = re.search(pattern, message)
                    if match:
                        candidate = match.group(1).strip()
                        if self._is_valid_alert_name(candidate):
                            logger.debug(f"Extracted alert name from message pattern: {candidate}")
                            return candidate
                
                # Fallback: Look for kubernetes/prometheus patterns
                k8s_patterns = [
                    r'(pod-[a-z0-9\-]+)',
                    r'(container-[a-z0-9\-]+)',
                    r'([a-z0-9\-]+prometheus[a-z0-9\-]*)',
                    r'([a-z0-9\-]+metrics[a-z0-9\-]*)',
                ]
                
                for pattern in k8s_patterns:
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        candidate = match.group(1)
                        if self._is_valid_alert_name(candidate):
                            logger.debug(f"Extracted alert name from k8s pattern: {candidate}")
                            return candidate
            
            # Strategy 3: Check alias field
            alias = self._safe_str(alert_data.get('alias', '')).strip()
            if alias and self._is_valid_alert_name(alias):
                logger.debug(f"Extracted alert name from alias: {alias}")
                return alias
            
            # Strategy 4: Extract from description
            description = self._safe_str(alert_data.get('description', '')).strip()
            if description:
                desc_patterns = [
                    r'Alert:\s*([A-Za-z0-9\-_]+)',
                    r'AlertName:\s*([A-Za-z0-9\-_]+)',
                    r'Rule:\s*([A-Za-z0-9\-_]+)',
                ]
                for pattern in desc_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        candidate = match.group(1).strip()
                        if self._is_valid_alert_name(candidate):
                            logger.debug(f"Extracted alert name from description: {candidate}")
                            return candidate
            
            # If all else fails, generate a name from available data
            tiny_id = self._safe_str(alert_data.get('tinyId', ''))
            if tiny_id:
                fallback_name = f"jsm-alert-{tiny_id}"
                logger.debug(f"Using fallback alert name: {fallback_name}")
                return fallback_name
            
            logger.warning(f"Could not extract alert name from JSM alert: {alert_data.get('id', 'unknown')}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting alert name from JSM alert: {e}")
            return None
    
    def extract_cluster_from_jsm(self, jsm_alert: Dict[str, Any]) -> Optional[str]:
        """Extract cluster information from JSM alert with comprehensive fallback."""
        try:
            alert_data = jsm_alert.get('data', jsm_alert)
            
            # Strategy 1: Check tags for cluster information
            tags = alert_data.get('tags', [])
            for tag in tags:
                if isinstance(tag, str):
                    # Direct cluster tag
                    if tag.startswith('cluster:'):
                        cluster = tag.split(':', 1)[1].strip()
                        if cluster and self._looks_like_cluster_name(cluster):
                            logger.debug(f"Extracted cluster from tag: {cluster}")
                            return cluster
                    
                    # Instance tag that may contain cluster info
                    if tag.startswith('instance:'):
                        instance = tag.split(':', 1)[1].strip()
                        cluster = self._extract_cluster_from_instance(instance)
                        if cluster:
                            logger.debug(f"Extracted cluster from instance tag: {cluster}")
                            return cluster
                    
                    # Look for cluster patterns in other tags
                    cluster_match = re.search(r'([a-zA-Z0-9\-_]*(?:prod|staging|dev|test)[a-zA-Z0-9\-_]*)', tag, re.IGNORECASE)
                    if cluster_match:
                        cluster = cluster_match.group(1)
                        if self._looks_like_cluster_name(cluster):
                            logger.debug(f"Extracted cluster from tag pattern: {cluster}")
                            return cluster
            
            # Strategy 2: Extract from message
            message = self._safe_str(alert_data.get('message', ''))
            cluster_patterns = [
                r'cluster[:\s]+([a-zA-Z0-9\-_]+)',
                r'datanode-\d+-([a-zA-Z0-9\-_]+)',
                r'([a-zA-Z0-9\-_]+)-cloud-',
                r'in\s+([a-zA-Z0-9\-_]+)\s+cluster',
            ]
            for pattern in cluster_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    cluster = match.group(1)
                    if self._looks_like_cluster_name(cluster):
                        logger.debug(f"Extracted cluster from message: {cluster}")
                        return cluster
            
            # Strategy 3: Check entity field
            entity = self._safe_str(alert_data.get('entity', '')).strip()
            if entity and self._looks_like_cluster_name(entity):
                logger.debug(f"Using entity as cluster: {entity}")
                return entity
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting cluster from JSM alert: {e}")
            return None
    
    def extract_severity_from_jsm(self, jsm_alert: Dict[str, Any]) -> Optional[str]:
        """Extract severity from JSM alert with proper priority mapping."""
        try:
            alert_data = jsm_alert.get('data', jsm_alert)
            
            # Strategy 1: Check priority field and map to severity
            priority = self._safe_str(alert_data.get('priority', '')).upper()
            priority_mapping = {
                'P1': 'critical',
                'P2': 'warning',
                'P3': 'info',
                'P4': 'low',
                'P5': 'info'
            }
            
            if priority in priority_mapping:
                severity = priority_mapping[priority]
                logger.debug(f"Mapped priority {priority} to severity: {severity}")
                return severity
            
            # Strategy 2: Check tags for severity keywords
            tags = alert_data.get('tags', [])
            severity_keywords = {
                'critical': ['critical', 'crit', 'p1', 'severity:critical'],
                'warning': ['warning', 'warn', 'p2', 'severity:warning'],
                'info': ['info', 'information', 'p3', 'p5', 'severity:info'],
                'low': ['low', 'minor', 'p4', 'severity:low']
            }
            
            for tag in tags:
                if isinstance(tag, str):
                    tag_lower = tag.lower()
                    for severity, keywords in severity_keywords.items():
                        if any(keyword in tag_lower for keyword in keywords):
                            logger.debug(f"Extracted severity from tag: {severity}")
                            return severity
            
            # Strategy 3: Check message/description for severity indicators  
            text_content = f"{alert_data.get('message', '')} {alert_data.get('description', '')}"
            text_lower = text_content.lower()
            
            for severity, keywords in severity_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    logger.debug(f"Extracted severity from text content: {severity}")
                    return severity
            
            # Default to 'info' if no severity found
            logger.debug("No severity found, defaulting to 'info'")
            return 'info'
            
        except Exception as e:
            logger.error(f"Error extracting severity from JSM alert: {e}")
            return 'info'
    
    def _extract_cluster_from_instance(self, instance: str) -> Optional[str]:
        """Extract cluster name from instance string."""
        if not instance:
            return None
        
        # Pattern: datanode-21-pro-cloud-shared-aws-us-east-1
        patterns = [
            r'^([a-zA-Z0-9\-_]+)-cloud-',  # Extract before '-cloud-'
            r'^([a-zA-Z0-9\-_]+)-\d+-',    # Extract before number
            r'^([a-zA-Z]+)',               # Just the first word
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instance)
            if match:
                cluster = match.group(1)
                if self._looks_like_cluster_name(cluster):
                    return cluster
        
        return None
    
    def _is_valid_alert_name(self, name: str) -> bool:
        """Validate if extracted text looks like a valid alert name."""
        if not name or len(name) < 3:
            return False
        
        # Check if it's not just generic text
        generic_patterns = [
            r'^(alert|error|warning|info|debug|message|notification)$',
            r'^\d+$',  # Just numbers
            r'^[^a-zA-Z]*$',  # No letters
            r'^(the|and|or|but|in|on|at|to|for|of|with|by)$',  # Common words
        ]
        
        for pattern in generic_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return False
        
        # Must contain at least some alphanumeric characters
        if not re.search(r'[a-zA-Z0-9]', name):
            return False
        
        return True
    
    def _looks_like_cluster_name(self, name: str) -> bool:
        """Check if a string looks like a cluster name."""
        if not name or len(name) < 2:
            return False
        
        # Common cluster name patterns
        cluster_indicators = [
            r'(prod|production|staging|stage|dev|development|test|testing)',
            r'(cluster|k8s|kubernetes)',
            r'(east|west|north|south|us|eu|asia)',
            r'(aws|azure|gcp|cloud)',
        ]
        
        # Must be alphanumeric with common separators
        if not re.match(r'^[a-zA-Z0-9\-_]+$', name):
            return False
        
        # Should contain cluster-related terms
        name_lower = name.lower()
        return any(re.search(pattern, name_lower) for pattern in cluster_indicators)
    
    async def acknowledge_jsm_alert(self, alert_id: str, note: str = None, user: str = None) -> bool:
        """Acknowledge a JSM alert"""
        try:
            cloud_id = await self.get_cloud_id()
            if not cloud_id:
                return False
            
            self._rate_limit()
            url = f"{self.base_url}/{cloud_id}/v1/alerts/{alert_id}/acknowledge"
            
            payload = {}
            if note:
                payload["note"] = note
            if user:
                payload["user"] = user
            
            response = requests.post(
                url, 
                headers=self.headers, 
                json=payload,
                timeout=getattr(settings, 'JSM_API_TIMEOUT', 30)
            )
            response.raise_for_status()
            
            logger.info(f"Successfully acknowledged JSM alert {alert_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error acknowledging JSM alert {alert_id}: {e}")
            return False
    
    async def close_jsm_alert(self, alert_id: str, note: str = None, user: str = None) -> bool:
        """Close a JSM alert"""
        try:
            cloud_id = await self.get_cloud_id()
            if not cloud_id:
                return False
            
            self._rate_limit()
            url = f"{self.base_url}/{cloud_id}/v1/alerts/{alert_id}/close"
            
            payload = {}
            if note:
                payload["note"] = note
            if user:
                payload["user"] = user
            
            response = requests.post(
                url, 
                headers=self.headers, 
                json=payload,
                timeout=getattr(settings, 'JSM_API_TIMEOUT', 30)
            )
            response.raise_for_status()
            
            logger.info(f"Successfully closed JSM alert {alert_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error closing JSM alert {alert_id}: {e}")
            return False
    
    def get_alert_status_info(self, jsm_alert: Dict) -> Dict[str, Any]:
        """Extract status information from JSM alert"""
        alert_data = jsm_alert.get('data', jsm_alert)
        
        return {
            'id': self._safe_str(alert_data.get('id')),
            'tiny_id': self._safe_str(alert_data.get('tinyId')),
            'status': self._safe_str(alert_data.get('status')),  # open, acked, closed
            'acknowledged': bool(alert_data.get('acknowledged', False)),
            'owner': self._safe_str(alert_data.get('owner')) or None,
            'priority': self._safe_str(alert_data.get('priority')) or None,
            'created_at': self._safe_str(alert_data.get('createdAt')) or None,
            'updated_at': self._safe_str(alert_data.get('updatedAt')) or None,
            'last_occurred_at': self._safe_str(alert_data.get('lastOccuredAt')) or None,
            'count': alert_data.get('count', 1),
            'tags': alert_data.get('tags', []),
            'alias': self._safe_str(alert_data.get('alias')) or None,
            'integration_name': self._safe_str(alert_data.get('integrationName')) or None,
            'source': self._safe_str(alert_data.get('source')) or None,
            'message': self._safe_str(alert_data.get('message', ''))
        }