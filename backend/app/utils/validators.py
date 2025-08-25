# Data validation utilities
from typing import Dict, Any, List

def validate_grafana_alert(alert: Dict[str, Any]) -> bool:
    """Validate Grafana alert structure"""
    required_fields = ['labels', 'startsAt']
    return all(field in alert for field in required_fields)

def validate_jsm_alert(alert: Dict[str, Any]) -> bool:
    """Validate JSM alert structure"""
    alert_data = alert.get('data', alert)
    required_fields = ['message', 'createdAt']
    return all(field in alert_data for field in required_fields)