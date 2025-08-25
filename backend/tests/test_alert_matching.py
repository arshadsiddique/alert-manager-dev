# tests/test_alert_matching.py - Comprehensive test suite

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

class TestAlertMatching(unittest.TestCase):
    
    def setUp(self):
        self.jsm_service = JSMService("test-api-key")
        self.matching_service = AlertMatchingService(confidence_threshold=0.70)
    
    def test_extract_alert_name_from_tags(self):
        """Test alert name extraction from JSM tags."""
        jsm_alert = {
            'data': {
                'tags': ['alertname:pod-not-healthy-prometheus-metrics-platform-k8s', 'cluster:prod'],
                'message': 'Test alert message'
            }
        }
        
        result = self.jsm_service.extract_alert_name_from_jsm(jsm_alert)
        self.assertEqual(result, 'pod-not-healthy-prometheus-metrics-platform-k8s')
    
    def test_extract_alert_name_from_message(self):
        """Test alert name extraction from JSM message."""
        jsm_alert = {
            'data': {
                'tags': [],
                'message': '[prod/monitoring] CPUHighUsage - CPU usage is above threshold'
            }
        }
        
        result = self.jsm_service.extract_alert_name_from_jsm(jsm_alert)
        self.assertEqual(result, 'CPUHighUsage')
    
    def test_high_confidence_match(self):
        """Test high confidence matching between similar alerts."""
        grafana_alert = {
            'labels': {
                'alertname': 'pod-not-healthy-prometheus-metrics-platform-k8s',
                'severity': 'critical',
                'cluster': 'prod-east'
            },
            'startsAt': '2025-06-26T10:00:00Z'
        }
        
        jsm_alert = {
            'data': {
                'tags': ['alertname:pod-not-healthy-prometheus-metrics-platform-k8s'],
                'priority': 'P1',
                'message': 'Pod not healthy in prometheus metrics platform',
                'createdAt': '2025-06-26T10:02:00Z',
                'details': {'cluster': 'prod-east'}
            }
        }
        
        confidence = self.matching_service.calculate_match_confidence(grafana_alert, jsm_alert)
        self.assertGreater(confidence, 0.85)
    
    def test_low_confidence_no_match(self):
        """Test that dissimilar alerts produce low confidence."""
        grafana_alert = {
            'labels': {
                'alertname': 'DiskSpaceWarning',
                'severity': 'warning'
            },
            'startsAt': '2025-06-26T10:00:00Z'
        }
        
        jsm_alert = {
            'data': {
                'message': 'Network connectivity issue',
                'priority': 'P2',
                'createdAt': '2025-06-26T12:00:00Z'
            }
        }
        
        confidence = self.matching_service.calculate_match_confidence(grafana_alert, jsm_alert)
        self.assertLess(confidence, 0.40)

if __name__ == '__main__':
    unittest.main()