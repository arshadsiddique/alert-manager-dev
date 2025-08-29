import requests
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from ..core.config import settings
import asyncio
import time

logger = logging.getLogger(__name__)

class PrometheusService:
    def __init__(self):
        # Parse API URLs from config
        self.api_urls = []
        if hasattr(settings, 'PROMETHEUS_API_URLS') and settings.PROMETHEUS_API_URLS:
            self.api_urls = [url.strip() for url in settings.PROMETHEUS_API_URLS.split(',') if url.strip()]
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        # Endpoint health tracking
        self.endpoint_health = {}  # Track which endpoints are working
        self.last_health_check = None
        self.health_check_interval = timedelta(minutes=5)  # Check health every 5 minutes
        
        logger.info(f"Initialized PrometheusService with {len(self.api_urls)} endpoint(s): {self.api_urls}")

    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Fetch all active alerts from all configured and healthy Prometheus instances."""
        all_alerts = []
        
        # Check if Prometheus sync is enabled
        if not getattr(settings, 'ENABLE_PROMETHEUS_SYNC', False):
            logger.info("Prometheus sync is disabled. Skipping fetch.")
            return all_alerts

        if not self.api_urls:
            logger.warning("No Prometheus API URLs configured. Check PROMETHEUS_API_URLS setting.")
            return all_alerts

        # Check endpoint health periodically
        await self._check_endpoint_health()
        
        # Get list of healthy endpoints
        healthy_endpoints = self._get_healthy_endpoints()
        
        if not healthy_endpoints:
            logger.error("No healthy Prometheus endpoints available!")
            return all_alerts

        logger.info(f"Using {len(healthy_endpoints)} healthy endpoint(s) out of {len(self.api_urls)} configured")
        
        # Fetch from all healthy endpoints
        for endpoint_info in healthy_endpoints:
            try:
                alerts = await self._fetch_from_healthy_endpoint(endpoint_info)
                
                if alerts:
                    logger.info(f"Retrieved {len(alerts)} active alerts from {endpoint_info['base_url']}")
                    all_alerts.extend(alerts)
                else:
                    logger.debug(f"No active alerts from {endpoint_info['base_url']}")
                
            except Exception as e:
                logger.error(f"Error fetching from healthy endpoint {endpoint_info['base_url']}: {e}")
                # Mark this endpoint as potentially unhealthy
                self._mark_endpoint_unhealthy(endpoint_info['base_url'], str(e))
                continue
        
        logger.info(f"Total Prometheus alerts collected: {len(all_alerts)} from {len(healthy_endpoints)} endpoint(s)")
        return all_alerts

    async def _check_endpoint_health(self):
        """Check and update the health status of all configured endpoints."""
        current_time = datetime.utcnow()
        
        # Skip health check if we checked recently
        if (self.last_health_check and 
            current_time - self.last_health_check < self.health_check_interval):
            return
        
        logger.info("Checking health of Prometheus endpoints...")
        self.last_health_check = current_time
        
        # Check each endpoint
        for base_url in self.api_urls:
            await self._check_single_endpoint_health(base_url)
        
        # Log health summary
        healthy_count = sum(1 for info in self.endpoint_health.values() if info['healthy'])
        logger.info(f"Endpoint health check completed: {healthy_count}/{len(self.api_urls)} endpoints healthy")

    async def _check_single_endpoint_health(self, base_url: str):
        """Check the health of a single endpoint."""
        endpoint_info = {
            'base_url': base_url,
            'healthy': False,
            'working_api_path': None,
            'last_check': datetime.utcnow(),
            'error': None,
            'response_time': None
        }
        
        # Try different API endpoints
        api_endpoints = ["/api/v1/alerts", "/api/v2/alerts"]
        
        for api_path in api_endpoints:
            try:
                url = f"{base_url.rstrip('/')}{api_path}"
                start_time = time.time()
                
                response = requests.get(url, headers=self.headers, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    # Validate that we get a proper response structure
                    data = response.json()
                    
                    # Check if the response has the expected structure
                    if api_path == "/api/v1/alerts":
                        # Prometheus API should have data.alerts
                        if isinstance(data.get('data', {}).get('alerts'), list):
                            endpoint_info.update({
                                'healthy': True,
                                'working_api_path': api_path,
                                'response_time': response_time,
                                'error': None
                            })
                            logger.info(f"✅ {base_url} is healthy (Prometheus API, {response_time:.2f}s)")
                            break
                    else:
                        # Alertmanager API should be a list
                        if isinstance(data, list):
                            endpoint_info.update({
                                'healthy': True,
                                'working_api_path': api_path,
                                'response_time': response_time,
                                'error': None
                            })
                            logger.info(f"✅ {base_url} is healthy (Alertmanager API, {response_time:.2f}s)")
                            break
                
                elif response.status_code == 404:
                    logger.debug(f"API path {api_path} not found on {base_url}")
                    continue
                else:
                    logger.debug(f"HTTP {response.status_code} from {base_url}{api_path}")
                    continue
                    
            except requests.Timeout:
                logger.debug(f"Timeout connecting to {base_url}{api_path}")
                endpoint_info['error'] = "Connection timeout"
                continue
            except requests.ConnectionError as e:
                logger.debug(f"Connection error to {base_url}{api_path}: {e}")
                endpoint_info['error'] = f"Connection error: {str(e)}"
                continue
            except Exception as e:
                logger.debug(f"Unexpected error checking {base_url}{api_path}: {e}")
                endpoint_info['error'] = f"Unexpected error: {str(e)}"
                continue
        
        # Store the endpoint info
        self.endpoint_health[base_url] = endpoint_info
        
        if not endpoint_info['healthy']:
            logger.warning(f"❌ {base_url} is unhealthy: {endpoint_info['error']}")

    def _get_healthy_endpoints(self) -> List[Dict[str, Any]]:
        """Get list of healthy endpoints."""
        healthy = []
        for base_url, info in self.endpoint_health.items():
            if info['healthy']:
                healthy.append(info)
        return healthy

    def _mark_endpoint_unhealthy(self, base_url: str, error: str):
        """Mark an endpoint as unhealthy."""
        if base_url in self.endpoint_health:
            self.endpoint_health[base_url].update({
                'healthy': False,
                'error': error,
                'last_check': datetime.utcnow()
            })
            logger.warning(f"Marked {base_url} as unhealthy: {error}")

    async def _fetch_from_healthy_endpoint(self, endpoint_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch alerts from a known healthy endpoint."""
        base_url = endpoint_info['base_url']
        api_path = endpoint_info['working_api_path']
        
        try:
            url = f"{base_url.rstrip('/')}{api_path}"
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse based on API type
            if api_path == "/api/v1/alerts":
                return self._parse_prometheus_api_response(data, base_url)
            else:
                return self._parse_alertmanager_api_response(data, base_url)
                
        except Exception as e:
            logger.error(f"Error fetching from {base_url}: {e}")
            raise

    def _parse_prometheus_api_response(self, data: Dict, source_instance: str) -> List[Dict[str, Any]]:
        """Parse Prometheus /api/v1/alerts response."""
        try:
            alerts = data.get('data', {}).get('alerts', [])
            parsed_alerts = []
            
            logger.debug(f"Processing {len(alerts)} alerts from Prometheus API")
            
            for alert in alerts:
                # Only include firing/active alerts
                state = alert.get('state', '').lower()
                if state != 'firing':
                    logger.debug(f"Skipping alert in state: {state}")
                    continue
                
                parsed_alert = self._parse_prometheus_alert(alert, source_instance)
                if parsed_alert:
                    parsed_alerts.append(parsed_alert)
            
            logger.info(f"Parsed {len(parsed_alerts)} firing alerts from Prometheus API at {source_instance}")
            return parsed_alerts
            
        except Exception as e:
            logger.error(f"Error parsing Prometheus API response from {source_instance}: {e}")
            return []

    def _parse_alertmanager_api_response(self, data: List, source_instance: str) -> List[Dict[str, Any]]:
        """Parse Alertmanager /api/v2/alerts response."""
        try:
            if not isinstance(data, list):
                logger.error(f"Expected list from Alertmanager API, got {type(data)}")
                return []
            
            parsed_alerts = []
            
            logger.debug(f"Processing {len(data)} alerts from Alertmanager API")
            
            for alert in data:
                # Only include active alerts
                status = alert.get('status', {})
                state = status.get('state', '').lower()
                
                if state != 'active':
                    logger.debug(f"Skipping alert in state: {state}")
                    continue
                
                parsed_alert = self._parse_alertmanager_alert(alert, source_instance)
                if parsed_alert:
                    parsed_alerts.append(parsed_alert)
            
            logger.info(f"Parsed {len(parsed_alerts)} active alerts from Alertmanager API at {source_instance}")
            return parsed_alerts
            
        except Exception as e:
            logger.error(f"Error parsing Alertmanager API response from {source_instance}: {e}")
            return []

    def _parse_prometheus_alert(self, alert: Dict[str, Any], source_instance: str) -> Dict[str, Any]:
        """Parse a single Prometheus alert."""
        try:
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            
            alert_name = labels.get('alertname', 'Unknown')
            instance = labels.get('instance', '')
            
            # Generate unique alert ID using fingerprint if available, otherwise hash
            fingerprint = str(hash(f"{alert_name}{instance}{labels.get('job', '')}{source_instance}"))
            alert_id = f"prometheus-{alert_name}-{fingerprint}"
            
            # Extract cluster information
            cluster = self._extract_cluster_info(labels, instance)
            
            # Extract severity
            severity = self._extract_severity(labels, annotations)
            
            # Get summary and description
            summary = self._extract_summary(labels, annotations, alert_name)
            description = annotations.get('description', annotations.get('summary', ''))
            
            parsed_alert = {
                'alert_id': alert_id,
                'alert_name': alert_name,
                'cluster': cluster,
                'pod': labels.get('pod', labels.get('kubernetes_pod_name')),
                'instance': instance,
                'severity': severity,
                'summary': summary,
                'description': description,
                'started_at': self._parse_datetime(alert.get('activeAt')),
                'generator_url': None,  # Not available in Prometheus API
                'labels': labels,
                'annotations': annotations,
                'source': 'prometheus',
                'source_instance': source_instance
            }
            
            logger.debug(f"✅ Parsed Prometheus alert: {alert_name} from {cluster or 'unknown cluster'}")
            return parsed_alert
            
        except Exception as e:
            logger.error(f"Error parsing Prometheus alert: {e}")
            logger.debug(f"Alert data: {alert}")
            return None

    def _parse_alertmanager_alert(self, alert: Dict[str, Any], source_instance: str) -> Dict[str, Any]:
        """Parse a single Alertmanager alert."""
        try:
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            
            alert_name = labels.get('alertname', 'Unknown')
            fingerprint = alert.get('fingerprint', str(hash(f"{str(labels)}{source_instance}")))
            
            alert_id = f"alertmanager-{alert_name}-{fingerprint}"
            
            # Extract cluster information
            instance = labels.get('instance', '')
            cluster = self._extract_cluster_info(labels, instance)
            
            # Extract severity
            severity = self._extract_severity(labels, annotations)
            
            # Get summary and description
            summary = self._extract_summary(labels, annotations, alert_name)
            description = annotations.get('description', '')
            
            parsed_alert = {
                'alert_id': alert_id,
                'alert_name': alert_name,
                'cluster': cluster,
                'pod': labels.get('pod', labels.get('kubernetes_pod_name')),
                'instance': instance,
                'severity': severity,
                'summary': summary,
                'description': description,
                'started_at': self._parse_datetime(alert.get('startsAt')),
                'generator_url': alert.get('generatorURL'),
                'labels': labels,
                'annotations': annotations,
                'source': 'prometheus',
                'source_instance': source_instance
            }
            
            logger.debug(f"✅ Parsed Alertmanager alert: {alert_name} from {cluster or 'unknown cluster'}")
            return parsed_alert
            
        except Exception as e:
            logger.error(f"Error parsing Alertmanager alert: {e}")
            logger.debug(f"Alert data: {alert}")
            return None

    def _extract_cluster_info(self, labels: Dict, instance: str) -> str:
        """Extract cluster information from labels or instance."""
        # Try various cluster label names
        cluster_labels = ['cluster', 'cluster_name', 'kubernetes_cluster', 'k8s_cluster', 'region']
        
        for label in cluster_labels:
            if label in labels and labels[label]:
                return labels[label]
        
        # Try to extract from instance string
        if instance:
            cluster = self._extract_cluster_from_instance(instance)
            if cluster:
                return cluster
        
        # Try to extract from other common labels
        if 'job' in labels:
            return labels['job']
        
        return None

    def _extract_severity(self, labels: Dict, annotations: Dict) -> str:
        """Extract severity from labels or annotations."""
        # Try labels first
        severity_labels = ['severity', 'priority', 'level']
        for label in severity_labels:
            if label in labels and labels[label]:
                return labels[label].lower()
        
        # Try annotations
        for label in severity_labels:
            if label in annotations and annotations[label]:
                return annotations[label].lower()
        
        return 'info'  # Default severity

    def _extract_summary(self, labels: Dict, annotations: Dict, alert_name: str) -> str:
        """Extract summary from annotations or generate one."""
        # Try annotations first
        summary_fields = ['summary', 'message', 'description']
        for field in summary_fields:
            if field in annotations and annotations[field]:
                return annotations[field]
        
        # Generate summary from alert name and labels
        if 'instance' in labels:
            return f"Alert {alert_name} on {labels['instance']}"
        elif 'job' in labels:
            return f"Alert {alert_name} in job {labels['job']}"
        else:
            return f"Prometheus alert: {alert_name}"

    def _extract_cluster_from_instance(self, instance: str) -> str:
        """Try to extract cluster information from instance string."""
        if not instance:
            return None
            
        import re
        
        # Common patterns for cluster extraction
        cluster_patterns = [
            r'[\w\-]*?(prod|production)[\w\-]*',
            r'[\w\-]*?(staging|stage)[\w\-]*',
            r'[\w\-]*?(dev|development)[\w\-]*',
            r'[\w\-]*?(test|testing)[\w\-]*',
            r'[\w\-]*?cluster[\w\-]*',
            r'[\w\-]*?k8s[\w\-]*',
            r'us-east[\w\-]*',
            r'us-west[\w\-]*',
            r'eu-[\w\-]*',
        ]
        
        for pattern in cluster_patterns:
            match = re.search(pattern, instance, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None

    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime string from Prometheus/Alertmanager."""
        if not date_str:
            return datetime.utcnow()
        try:
            # Handle RFC3339 format with nanoseconds
            if '.' in date_str and 'Z' in date_str:
                # Remove nanoseconds, keep microseconds
                date_parts = date_str.split('.')
                if len(date_parts) == 2:
                    nanoseconds = date_parts[1].rstrip('Z')
                    # Keep only first 6 digits (microseconds)
                    microseconds = nanoseconds[:6].ljust(6, '0')
                    date_str = f"{date_parts[0]}.{microseconds}Z"
            
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError as e:
            logger.warning(f"Failed to parse datetime '{date_str}': {e}")
            return datetime.utcnow()

    def get_endpoint_health_status(self) -> Dict[str, Any]:
        """Get the current health status of all endpoints."""
        return {
            'total_endpoints': len(self.api_urls),
            'healthy_endpoints': len([info for info in self.endpoint_health.values() if info['healthy']]),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'endpoints': self.endpoint_health
        }

    def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to all configured Prometheus endpoints (synchronous version)."""
        results = {
            'total_endpoints': len(self.api_urls),
            'successful_endpoints': 0,
            'failed_endpoints': 0,
            'endpoint_results': []
        }
        
        for base_url in self.api_urls:
            endpoint_result = {
                'url': base_url,
                'status': 'unknown',
                'working_endpoint': None,
                'error': None,
                'alert_count': 0
            }
            
            # Try different API endpoints
            api_endpoints = ["/api/v1/alerts", "/api/v2/alerts"]
            
            for api_path in api_endpoints:
                try:
                    url = f"{base_url.rstrip('/')}{api_path}"
                    response = requests.get(url, headers=self.headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Count alerts based on API type
                        if api_path == "/api/v1/alerts":
                            alerts = data.get('data', {}).get('alerts', [])
                            active_alerts = [a for a in alerts if a.get('state') == 'firing']
                        else:
                            alerts = data if isinstance(data, list) else []
                            active_alerts = [a for a in alerts if a.get('status', {}).get('state') == 'active']
                        
                        endpoint_result['status'] = 'success'
                        endpoint_result['working_endpoint'] = api_path
                        endpoint_result['alert_count'] = len(active_alerts)
                        results['successful_endpoints'] += 1
                        break
                        
                except Exception as e:
                    endpoint_result['error'] = f"{api_path}: {str(e)}"
                    continue
            
            if endpoint_result['status'] == 'unknown':
                endpoint_result['status'] = 'failed'
                results['failed_endpoints'] += 1
            
            results['endpoint_results'].append(endpoint_result)
        
        return results