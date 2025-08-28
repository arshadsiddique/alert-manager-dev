from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    # --- Prometheus Alertmanager Configuration (NEW) ---
    ENABLE_PROMETHEUS_SYNC: bool = True
    PROMETHEUS_API_URLS: str = "http://monitoring-awseu.devo.internal:9090,http://monitoring-awsus.devo.internal:9090"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/alertdb"
    
    # Grafana
    GRAFANA_API_URL: str = "https://grafana.observability.devo.com"
    GRAFANA_API_KEY: str = ""
    
    # JSM (Jira Service Management) API Settings
    JIRA_URL: str = "https://devoinc.atlassian.net"  # Your Atlassian instance URL
    JIRA_USER_EMAIL: str = ""                        # Your email address
    JIRA_API_TOKEN: str = ""                         # Your Atlassian API token
    
    # JSM Cloud ID (will be auto-retrieved if not provided)
    JSM_CLOUD_ID: Optional[str] = None               # UUID format cloud ID
    
    # JSM API Configuration
    JSM_API_BASE_URL: str = "https://api.atlassian.com/jsm/ops/api"
    JSM_ALERTS_LIMIT: int = 500                      # Max alerts to fetch per request
    
    # Alert Matching Configuration (UPDATED)
    ALERT_MATCH_CONFIDENCE_THRESHOLD: float = 70.0      # Increased from 15.0
    ALERT_MATCH_HIGH_CONFIDENCE_THRESHOLD: float = 85.0  # NEW
    ALERT_MATCH_MANUAL_REVIEW_THRESHOLD: float = 60.0    # NEW
    ALERT_MATCH_TIME_WINDOW_MINUTES: int = 15            # Keep existing
    ALERT_MATCH_MAX_TIME_WINDOW_HOURS: int = 24          # NEW

    # Enhanced Matching Features (NEW)
    ENABLE_FUZZY_MATCHING: bool = True
    ENABLE_CONTENT_SIMILARITY: bool = True
    ENABLE_TEMPORAL_CORRELATION: bool = True
    ENABLE_ADVANCED_CLUSTERING: bool = True             # Enable fuzzy string matching
    ENABLE_TIME_PROXIMITY_MATCHING: bool = True     # Use time proximity for matching
    ENABLE_CONTENT_SIMILARITY_MATCHING: bool = True # Use content similarity for matching
    
    # Sync Configuration
    GRAFANA_SYNC_INTERVAL_SECONDS: int = 300         # Sync every 5 minutes
    JSM_SYNC_INTERVAL_SECONDS: int = 300             # Sync JSM alerts every 5 minutes
    
    # Alert Filtering (Updated for better production filtering)
    FILTER_NON_PROD_ALERTS: bool = True              # Filter out non-production alerts
    EXCLUDED_CLUSTERS: list = ["stage", "dev", "test", "staging", "development"]  # Extended list
    EXCLUDED_ENVIRONMENTS: list = ["devo-stage-eu", "staging", "development", "dev"]  # Extended list
    
    # App
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]
    
    # Legacy Jira Settings (deprecated but kept for backwards compatibility)
    JIRA_PROJECT_KEY: str = "OP"                     # Not used in JSM mode
    JIRA_INCIDENT_ISSUE_TYPE: str = "Incident"      # Not used in JSM mode
    JIRA_ACKNOWLEDGE_TRANSITION_NAME: str = "To Do" # Not used in JSM mode
    JIRA_RESOLVE_TRANSITION_NAME: str = "Completed" # Not used in JSM mode
    
    # Feature Flags (Updated)
    USE_JSM_MODE: bool = True                        # Use JSM API instead of Jira issues
    ENABLE_AUTO_CLOSE: bool = True                   # Auto-close JSM alerts when Grafana resolves
    ENABLE_MATCH_LOGGING: bool = True                # Enable detailed matching logs for debugging
    
    # Matching Weights (for fine-tuning matching algorithm)
    MATCH_WEIGHT_ALERT_NAME: int = 40               # Weight for alert name matching
    MATCH_WEIGHT_CLUSTER: int = 25                  # Weight for cluster matching
    MATCH_WEIGHT_SEVERITY: int = 15                 # Weight for severity matching
    MATCH_WEIGHT_CONTENT: int = 20                  # Weight for content similarity
    MATCH_WEIGHT_TIME_PROXIMITY: int = 10           # Weight for time proximity
    MATCH_WEIGHT_SOURCE: int = 15                   # Weight for JSM source being Grafana
    
    # Performance Settings
    MAX_ALERTS_TO_PROCESS: int = 5000               # Max alerts to process in one sync
    BATCH_SIZE_ALERTS: int = 100                    # Process alerts in batches

    # JSM API Configuration (ENHANCED)
    JSM_API_TIMEOUT: int = 30
    JSM_MAX_RETRIES: int = 3
    JSM_RETRY_DELAY: int = 5
    JSM_RATE_LIMIT_PER_MINUTE: int = 5000
    
    # Matching Performance Settings (NEW)
    MAX_ALERTS_PER_MATCHING_BATCH: int = 5000
    MATCHING_PROCESSING_TIMEOUT_SECONDS: int = 300
    ENABLE_MATCHING_CACHE: bool = True
    MATCHING_CACHE_TTL_MINUTES: int = 30
    
    # Logging and Debugging (NEW)
    LOG_MATCHING_DETAILS: bool = True
    SAVE_MATCHING_METRICS: bool = True
    DEBUG_MATCHING_ENABLED: bool = False

    ALLOWED_ORIGINS: list = [
        "https://dam.int.devo.com",
        "https://api-dam.int.devo.com",
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()