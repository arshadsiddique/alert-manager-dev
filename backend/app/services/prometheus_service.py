import requests
import logging
from typing import List, Dict, Any
from datetime import datetime
from ..core.config import settings

logger = logging.getLogger(__name__)

class PrometheusService:
    def __init__(self):
        self.api_urls = [url.strip() for url in settings.PROMETHEUS_API_URLS.split(',') if url.strip()]
        self.headers = {
            "Content-Type": "application/json"
        }

    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Fetch all active alerts from all configured Prometheus Alertmanager instances."""
        all_alerts = []
        if not settings.ENABLE_PROMETHEUS_SYNC:
            logger.info("Prometheus sync is disabled. Skipping fetch.")
            return all_alerts

        logger.info(f"Fetching alerts from {len(self.api_urls)} Prometheus Alertmanager instance(s).")
        for base_url in self.api_urls:
            try:
                url = f"{base_url}/api/v2/alerts"
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                alerts = response.json()
                active_alerts = [self._parse_alert(alert, base_url) for alert in alerts if alert.get('status', {}).get('state') == 'active']
                
                logger.info(f"Found {len(active_alerts)} active alerts in Prometheus at {base_url}")
                all_alerts.extend(active_alerts)
                
            except requests.RequestException as e:
                logger.error(f"Error fetching alerts from Prometheus Alertmanager at {base_url}: {e}")
                continue
        
        return all_alerts

    def _parse_alert(self, alert: Dict[str, Any], source_instance: str) -> Dict[str, Any]:
        """Parse Prometheus alert data into our standard format."""
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        return {
            'alert_id': f"{labels.get('alertname', '')}-{alert.get('fingerprint', '')}",
            'alert_name': labels.get('alertname', 'Unnamed Prometheus Alert'),
            'cluster': labels.get('cluster'),
            'pod': labels.get('pod'),
            'severity': labels.get('severity'),
            'summary': annotations.get('summary') or annotations.get('message'),
            'description': annotations.get('description', ''),
            'started_at': self._parse_datetime(alert.get('startsAt')),
            'generator_url': alert.get('generatorURL'),
            'labels': labels,
            'annotations': annotations,
            'source': 'prometheus', # Add the source
            'source_instance': source_instance # Track which prometheus instance
        }

    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime string from Prometheus."""
        if not date_str:
            return datetime.utcnow()
        try:
            # Handle RFC3339 format with nanoseconds
            if '.' in date_str and 'Z' in date_str:
                date_str = date_str.split('.')[0] + 'Z'
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return datetime.utcnow()