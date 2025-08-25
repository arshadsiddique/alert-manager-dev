from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CronConfigBase(BaseModel):
    job_name: str
    cron_expression: str
    is_enabled: bool = True

class CronConfigCreate(CronConfigBase):
    pass

class CronConfigUpdate(BaseModel):
    cron_expression: Optional[str] = None
    is_enabled: Optional[bool] = None

class CronConfigResponse(CronConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
