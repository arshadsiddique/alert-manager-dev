from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import csv
import io
from ...core.database import get_db
from ...services.alert_service import AlertService
from ...schemas.alert import AlertResponse, AcknowledgeRequest, ResolveRequest

router = APIRouter()
alert_service = AlertService()

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    """
    Get paginated list of Grafana alerts that have been successfully matched 
    with a JSM alert.
    """
    alerts = alert_service.get_alerts(db, skip=skip, limit=limit)
    return alerts

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get specific alert by ID"""
    alert = alert_service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/acknowledge")
async def acknowledge_alerts(
    request: AcknowledgeRequest,
    db: Session = Depends(get_db)
):
    """Acknowledge alerts in Jira"""
    success = await alert_service.acknowledge_alerts(
        db, request.alert_ids, request.note, request.acknowledged_by
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to acknowledge alerts")
    return {"message": "Alerts acknowledged successfully"}

@router.post("/resolve")
async def resolve_alerts(
    request: ResolveRequest,
    db: Session = Depends(get_db)
):
    """Manually resolve alerts in Jira"""
    success = await alert_service.resolve_alerts(
        db, request.alert_ids, request.note, request.resolved_by
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to resolve alerts")
    return {"message": "Alerts resolved successfully"}

@router.post("/sync")
async def sync_alerts(db: Session = Depends(get_db)):
    """Manually trigger alert sync"""
    await alert_service.sync_alerts(db)
    return {"message": "Alert sync completed"}

# === CSV Export Endpoints ===

@router.get("/export/csv")
async def export_alerts_csv(
    severity: Optional[List[str]] = Query(None),
    grafana_status: Optional[List[str]] = Query(None),
    jira_status: Optional[List[str]] = Query(None),
    cluster: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    include_resolved: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Export alerts to CSV format with optional filtering"""
    try:
        # Parse date filters
        filters = {}
        if severity:
            filters['severity'] = severity
        if grafana_status:
            filters['grafana_status'] = grafana_status
        if jira_status:
            filters['jira_status'] = jira_status
        if cluster:
            filters['cluster'] = cluster
        if date_from:
            try:
                filters['date_from'] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format")
        if date_to:
            try:
                filters['date_to'] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format")
        
        # If not including resolved, filter them out
        if not include_resolved:
            if 'jira_status' not in filters:
                filters['jira_status'] = []
            if isinstance(filters['jira_status'], list):
                # Remove resolved status if present
                filters['jira_status'] = [s for s in filters['jira_status'] if s != 'resolved']
                # If empty list after filtering, set to non-resolved statuses
                if not filters['jira_status']:
                    filters['jira_status'] = ['open', 'acknowledged']
        
        # Get alerts for export
        alerts = alert_service.get_alerts_for_export(db, filters)
        
        # Create CSV content
        def generate_csv():
            output = io.StringIO()
            writer = csv.writer(output)
            
            # CSV Headers
            headers = [
                'Alert ID', 'Alert Name', 'Cluster', 'Pod', 'Severity', 
                'Summary', 'Description', 'Grafana Status', 'Jira Status',
                'Jira Issue Key', 'Jira Issue URL', 'Jira Assignee', 'Jira Assignee Email',
                'Acknowledged By', 'Acknowledged At', 'Resolved By', 'Resolved At',
                'Started At', 'Created At', 'Updated At', 'Generator URL'
            ]
            writer.writerow(headers)
            
            # Write alert data
            for alert in alerts:
                row = [
                    alert.alert_id or '',
                    alert.alert_name or '',
                    alert.cluster or '',
                    alert.pod or '',
                    alert.severity or '',
                    (alert.summary or '').replace('\n', ' ').replace('\r', ' '),
                    (alert.description or '').replace('\n', ' ').replace('\r', ' '),
                    alert.grafana_status or '',
                    alert.jira_status or '',
                    alert.jira_issue_key or '',
                    alert.jira_issue_url or '',
                    alert.jira_assignee or '',
                    alert.jira_assignee_email or '',
                    alert.acknowledged_by or '',
                    alert.acknowledged_at.isoformat() if alert.acknowledged_at else '',
                    alert.resolved_by or '',
                    alert.resolved_at.isoformat() if alert.resolved_at else '',
                    alert.started_at.isoformat() if alert.started_at else '',
                    alert.created_at.isoformat() if alert.created_at else '',
                    alert.updated_at.isoformat() if alert.updated_at else '',
                    alert.generator_url or ''
                ]
                writer.writerow(row)
            
            output.seek(0)
            return output.getvalue()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"alerts_export_{timestamp}.csv"
        
        # Create response
        csv_content = generate_csv()
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/summary")
async def export_summary(db: Session = Depends(get_db)):
    """Get export summary statistics"""
    try:
        all_alerts = alert_service.get_alerts_for_export(db)
        
        # Calculate statistics
        total = len(all_alerts)
        by_severity = {}
        by_status = {}
        by_cluster = {}
        
        for alert in all_alerts:
            # Count by severity
            severity = alert.severity or 'unknown'
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Count by status
            status = alert.jira_status or 'unknown'
            by_status[status] = by_status.get(status, 0) + 1
            
            # Count by cluster
            cluster = alert.cluster or 'unknown'
            by_cluster[cluster] = by_cluster.get(cluster, 0) + 1
        
        return {
            "total_alerts": total,
            "by_severity": by_severity,
            "by_jira_status": by_status,
            "by_cluster": by_cluster,
            "available_filters": {
                "severities": list(by_severity.keys()),
                "statuses": list(by_status.keys()),
                "clusters": list(by_cluster.keys())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")