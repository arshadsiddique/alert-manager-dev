from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import engine, Base
from .api.routes import alerts, config
from .services.jsm_service import JSMService
import logging
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scheduler instance
global_scheduler = None

app = FastAPI(
    title="Devo Alert Manager API",
    description="API for managing Grafana alerts with Jira Service Management (JSM) integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dam.int.devo.com",          # production frontend
        "https://api-dam.int.devo.com",      # backend (for docs/redoc)
        "http://localhost:3000",             # Local development frontend
        "http://localhost:8000",             # Local development backend
    ] + (["*"] if settings.DEBUG else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def handle_proxy_headers(request, call_next):
    # Handle X-Forwarded-Proto from nginx ingress
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto
    if forwarded_host:
        request.scope["server"] = (forwarded_host, None)
    
    response = await call_next(request)
    
    # Add CORS headers for preflight requests
    if request.method == "OPTIONS":
        response.headers["Access-Control-Allow-Origin"] = "https://dam.int.devo.com"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# Include routers
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(config.router, prefix="/api/config", tags=["config"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global global_scheduler
    
    try:
        logger.info("🚀 Starting Devo Alert Manager API v1.0.0")
        
        # Create database tables
        logger.info("📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
        # Test JSM connectivity
        if settings.USE_JSM_MODE:
            logger.info("🔌 Testing JSM connectivity...")
            jsm_service = JSMService()
            try:
                cloud_id = await jsm_service.get_cloud_id()
                if cloud_id:
                    logger.info(f"✅ JSM connectivity successful - Cloud ID: {cloud_id}")
                    
                    # Test fetching alerts
                    test_alerts = await jsm_service.get_jsm_alerts(limit=1)
                    logger.info(f"✅ JSM Alerts API accessible - Found {len(test_alerts)} alerts in test")
                else:
                    logger.error("❌ Failed to retrieve JSM Cloud ID")
            except Exception as e:
                logger.error(f"❌ JSM connectivity test failed: {e}")
                logger.warning("⚠️  JSM integration may not work properly")
        else:
            logger.info("ℹ️  JSM mode disabled - running in legacy mode")
        
        # Create default cron job if none exist
        from .core.database import SessionLocal
        from .models.config import CronConfig
        
        db = SessionLocal()
        try:
            existing_jobs = db.query(CronConfig).count()
            if existing_jobs == 0:
                # Create default job with shorter interval for JSM mode
                interval = "*/5 * * * *" if settings.USE_JSM_MODE else "*/15 * * * *"
                default_job = CronConfig(
                    job_name="alert-sync",
                    cron_expression=interval,
                    is_enabled=True
                )
                db.add(default_job)
                db.commit()
                logger.info(f"✅ Created default alert-sync cron job ({interval})")
            else:
                logger.info(f"📋 Found {existing_jobs} existing cron jobs")
        except Exception as e:
            logger.error(f"❌ Error creating default job: {e}")
        finally:
            db.close()
        
        # Initialize scheduler after tables are ready
        from .services.scheduler_service import SchedulerService
        global_scheduler = SchedulerService()
        global_scheduler.ensure_jobs_loaded()
        logger.info("✅ Scheduler service initialized")
        
        # Log configuration summary
        logger.info("📋 Configuration Summary:")
        logger.info(f"   • JSM Mode: {'Enabled' if settings.USE_JSM_MODE else 'Disabled (Legacy)'}")
        logger.info(f"   • Jira URL: {settings.JIRA_URL}")
        logger.info(f"   • Grafana URL: {settings.GRAFANA_API_URL}")
        logger.info(f"   • Auto-close JSM Alerts: {'Enabled' if settings.ENABLE_AUTO_CLOSE else 'Disabled'}")
        logger.info(f"   • Debug Mode: {'Enabled' if settings.DEBUG else 'Disabled'}")
        
        if settings.USE_JSM_MODE:
            logger.info(f"   • JSM Cloud ID: {settings.JSM_CLOUD_ID or 'Auto-detect'}")
            logger.info(f"   • Match Confidence Threshold: {settings.ALERT_MATCH_CONFIDENCE_THRESHOLD}%")
            logger.info(f"   • Match Time Window: {settings.ALERT_MATCH_TIME_WINDOW_MINUTES} minutes")
        
        logger.info("🎉 Devo Alert Manager API started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global global_scheduler
    
    logger.info("🛑 Shutting down Devo Alert Manager API...")
    
    if global_scheduler:
        try:
            global_scheduler.scheduler.shutdown()
            logger.info("✅ Scheduler stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
    
    logger.info("👋 Shutdown complete")

def get_global_scheduler():
    """Get the global scheduler instance"""
    return global_scheduler

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Devo Alert Manager API", 
        "version": "1.0.0",
        "status": "running",
        "mode": "JSM Integration" if settings.USE_JSM_MODE else "Legacy Jira",
        "jira_url": settings.JIRA_URL,
        "grafana_url": settings.GRAFANA_API_URL,
        "features": {
            "jsm_mode": settings.USE_JSM_MODE,
            "auto_close": settings.ENABLE_AUTO_CLOSE,
            "debug": settings.DEBUG
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "grafana-jsm-alert-manager-api",
        "version": "1.0.0",
        "mode": "JSM" if settings.USE_JSM_MODE else "Legacy"
    }
    
    # Add JSM connectivity check in JSM mode
    if settings.USE_JSM_MODE:
        try:
            jsm_service = JSMService()
            cloud_id = await jsm_service.get_cloud_id()
            health_status["jsm_connectivity"] = "ok" if cloud_id else "error"
            health_status["jsm_cloud_id"] = cloud_id
        except Exception as e:
            health_status["jsm_connectivity"] = "error"
            health_status["jsm_error"] = str(e)
    
    # Add scheduler status
    if global_scheduler:
        health_status["scheduler"] = "running" if global_scheduler.scheduler.running else "stopped"
    else:
        health_status["scheduler"] = "not_initialized"
    
    return health_status

@app.get("/api/info")
async def get_api_info():
    """Get API information and capabilities"""
    from .core.database import SessionLocal
    from .models.alert import Alert
    
    db = SessionLocal()
    try:
        total_alerts = db.query(Alert).count()
        if settings.USE_JSM_MODE:
            matched_alerts = db.query(Alert).filter(Alert.jsm_alert_id.isnot(None)).count()
            match_rate = round((matched_alerts / total_alerts * 100) if total_alerts > 0 else 0, 1)
        else:
            matched_alerts = 0
            match_rate = 0
            
    except Exception:
        total_alerts = 0
        matched_alerts = 0
        match_rate = 0
    finally:
        db.close()
    
    return {
        "api_version": "1.0.0",
        "mode": "JSM Integration" if settings.USE_JSM_MODE else "Legacy Jira",
        "capabilities": {
            "jsm_integration": settings.USE_JSM_MODE,
            "alert_matching": settings.USE_JSM_MODE,
            "auto_close": settings.ENABLE_AUTO_CLOSE,
            "csv_export": True,
            "bulk_operations": True,
            "real_time_sync": True
        },
        "statistics": {
            "total_alerts": total_alerts,
            "matched_alerts": matched_alerts,
            "match_rate_percentage": match_rate
        },
        "configuration": {
            "sync_interval": f"{settings.GRAFANA_SYNC_INTERVAL_SECONDS}s",
            "match_threshold": f"{settings.ALERT_MATCH_CONFIDENCE_THRESHOLD}%" if settings.USE_JSM_MODE else None,
            "time_window": f"{settings.ALERT_MATCH_TIME_WINDOW_MINUTES}m" if settings.USE_JSM_MODE else None
        }
    }

# Add middleware for request logging in debug mode
if settings.DEBUG:
    @app.middleware("http")
    async def log_requests(request, call_next):
        import time
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
        return response

# Add error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "detail": str(exc) if settings.DEBUG else "An error occurred"
    }