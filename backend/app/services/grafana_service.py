import requests
import logging
from typing import List, Dict, Any
from datetime import datetime
from ..core.config import settings

logger = logging.getLogger(__name__)

class GrafanaService:
    def __init__(self):
        self.base_url = settings.GRAFANA_API_URL
        self.api_key = settings.GRAFANA_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Fetch all active alerts from Grafana"""
        try:
            url = f"{self.base_url}/api/alertmanager/grafana/api/v2/alerts"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            alerts = response.json()
            active_alerts = []
            
            for alert in alerts:
                state = alert.get('status', {}).get('state')
                if state == 'active':
                    active_alerts.append(self._parse_alert(alert))
            
            logger.info(f"Found {len(active_alerts)} active alerts in Grafana")
            return active_alerts
            
        except requests.RequestException as e:
            logger.error(f"Error fetching alerts from Grafana: {e}")
            return []
    
    def _parse_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Grafana alert data"""
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        return {
            'alert_id': f"{labels.get('alertname', '')}-{alert.get('fingerprint', '')}",
            'alert_name': labels.get('alertname', 'Unnamed'),
            'cluster': labels.get('cluster'),
            'pod': labels.get('pod'),
            'severity': labels.get('severity'),
            'summary': annotations.get('summary'),
            'description': annotations.get('description', ''),
            'started_at': self._parse_datetime(alert.get('startsAt')),
            'generator_url': alert.get('generatorURL'),
            'labels': labels,
            'annotations': annotations
        }
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime string from Grafana"""
        if not date_str:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return datetime.utcnow()
