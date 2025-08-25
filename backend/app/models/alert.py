from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, Float
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
from ..core.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    # Core alert fields from Grafana
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True)
    alert_name = Column(String, index=True)
    cluster = Column(String, index=True)
    pod = Column(String)
    severity = Column(String, index=True)
    summary = Column(Text)
    description = Column(Text)
    started_at = Column(DateTime)
    generator_url = Column(String)
    grafana_status = Column(String, default="active", index=True)
    labels = Column(JSON)
    annotations = Column(JSON)
    
    # JSM Alert Integration Fields
    jsm_alert_id = Column(String, nullable=True, index=True)
    jsm_tiny_id = Column(String, nullable=True, index=True)
    jsm_status = Column(String, nullable=True, index=True)
    jsm_acknowledged = Column(Boolean, default=False, index=True)
    jsm_owner = Column(String, nullable=True)
    jsm_priority = Column(String, nullable=True)
    jsm_alias = Column(String, nullable=True)
    jsm_integration_name = Column(String, nullable=True)
    jsm_source = Column(String, nullable=True)
    jsm_count = Column(Integer, default=1)
    jsm_tags = Column(JSON, nullable=True)
    jsm_last_occurred_at = Column(DateTime, nullable=True)
    jsm_created_at = Column(DateTime, nullable=True)
    jsm_updated_at = Column(DateTime, nullable=True)
    
    # Matching Information
    match_type = Column(String, nullable=True, index=True)
    match_confidence = Column(Float, nullable=True)
    match_score = Column(Float, nullable=True, index=True)
    match_details = Column(JSON, nullable=True)
    manual_review_required = Column(Boolean, default=False, index=True)
    matching_timestamp = Column(DateTime, nullable=True)
    
    # Manual Actions (for tracking manual interventions)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Legacy Jira fields (keeping for backwards compatibility)
    jira_status = Column(String, default="open", index=True)
    jira_issue_key = Column(String, nullable=True)
    jira_issue_id = Column(String, nullable=True)
    jira_issue_url = Column(String, nullable=True)
    jira_assignee = Column(String, nullable=True)
    jira_assignee_email = Column(String, nullable=True)
    
    # System fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @property
    def effective_status(self):
        """Get the effective status (prioritize JSM over legacy Jira)"""
        if self.jsm_status:
            return self.jsm_status
        return self.jira_status or "open"
    
    @property
    def effective_assignee(self):
        """Get the effective assignee (prioritize JSM over legacy Jira)"""
        return self.jsm_owner or self.jira_assignee
    
    @property
    def is_acknowledged(self):
        """Check if alert is acknowledged in any system"""
        return (
            self.jsm_acknowledged or 
            self.acknowledged_by is not None or
            self.effective_status in ['acked', 'acknowledged']
        )
    
    @property
    def is_resolved(self):
        """Check if alert is resolved/closed"""
        return (
            self.grafana_status == 'resolved' or
            self.effective_status in ['closed', 'resolved']
        )

    @property
    def match_quality(self):
        """Get match quality category"""
        if not self.match_confidence:
            return 'no_match'
        elif self.match_confidence >= 85:
            return 'high_confidence'
        elif self.match_confidence >= 70:
            return 'good_match'
        elif self.match_confidence >= 60:
            return 'manual_review'
        else:
            return 'low_confidence'
