from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

class AlertBase(BaseModel):
    alert_name: str
    cluster: Optional[str] = None
    pod: Optional[str] = None
    severity: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None

class AlertCreate(AlertBase):
    alert_id: str
    started_at: Optional[datetime] = None
    generator_url: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None

class AlertUpdate(BaseModel):
    grafana_status: Optional[str] = None
    jira_status: Optional[str] = None
    jsm_status: Optional[str] = None
    jsm_acknowledged: Optional[bool] = None

class AlertResponse(AlertBase):
    id: int
    alert_id: str
    started_at: Optional[datetime]
    generator_url: Optional[str]
    grafana_status: str
    
    # Legacy fields
    jira_status: str
    jira_issue_key: Optional[str]
    jira_assignee: Optional[str]
    
    # JSM fields
    jsm_alert_id: Optional[str]
    jsm_tiny_id: Optional[str]
    jsm_status: Optional[str]
    jsm_acknowledged: Optional[bool]
    jsm_owner: Optional[str]
    jsm_priority: Optional[str]
    jsm_source: Optional[str]
    jsm_count: Optional[int]
    jsm_tags: Optional[List[str]]
    jsm_created_at: Optional[datetime]
    jsm_updated_at: Optional[datetime]
    
    # Matching info
    match_type: Optional[str]
    match_confidence: Optional[float]
    
    # Actions
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    
    # System fields
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AcknowledgeRequest(BaseModel):
    alert_ids: List[int]
    note: Optional[str] = None
    acknowledged_by: Optional[str] = "System User"

class ResolveRequest(BaseModel):
    alert_ids: List[int]
    note: Optional[str] = None
    resolved_by: Optional[str] = "System User"
