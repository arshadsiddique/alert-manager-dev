from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
from ..core.database import Base

class CronConfig(Base):
    __tablename__ = "cron_config"
    
    id = Column(Integer, primary_key=True)
    job_name = Column(String, unique=True)
    cron_expression = Column(String, default="*/5 * * * *")
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
