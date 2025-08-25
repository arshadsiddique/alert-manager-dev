from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...core.database import get_db
from ...models.config import CronConfig
from ...schemas.config import CronConfigResponse, CronConfigCreate, CronConfigUpdate

router = APIRouter()

def get_scheduler_service():
    """Get scheduler service instance - lazy loading"""
    from ...main import get_global_scheduler
    scheduler = get_global_scheduler()
    if scheduler is None:
        from ...services.scheduler_service import SchedulerService
        return SchedulerService()
    return scheduler

@router.get("/cron", response_model=List[CronConfigResponse])
async def get_cron_configs(db: Session = Depends(get_db)):
    """Get all cron configurations"""
    try:
        scheduler_service = get_scheduler_service()
        if scheduler_service:
            scheduler_service.ensure_jobs_loaded()
        return db.query(CronConfig).all()
    except Exception as e:
        return []

@router.post("/cron", response_model=CronConfigResponse)
async def create_cron_config(
    config: CronConfigCreate,
    db: Session = Depends(get_db)
):
    """Create new cron configuration"""
    db_config = CronConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    try:
        scheduler_service = get_scheduler_service()
        if scheduler_service and db_config.is_enabled:
            scheduler_service._add_job(db_config)
    except Exception as e:
        print(f"Warning: Could not add job to scheduler: {e}")
    
    return db_config

@router.put("/cron/{config_id}", response_model=CronConfigResponse)
async def update_cron_config(
    config_id: int,
    config: CronConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update cron configuration"""
    db_config = db.query(CronConfig).filter(CronConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    update_data = config.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    
    try:
        scheduler_service = get_scheduler_service()
        if scheduler_service:
            if db_config.is_enabled:
                scheduler_service.update_job(db_config.job_name, db_config.cron_expression)
            else:
                scheduler_service.remove_job(db_config.job_name)
    except Exception as e:
        print(f"Warning: Could not update job in scheduler: {e}")
    
    return db_config
