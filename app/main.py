"""
FastAPI Main Application
Maintains backward compatibility with Flask routes
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging

from app.api.routes import router
from app.tasks.bsr_tasks import update_all_worksheets_bsr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Amazon BSR Tracking API",
    description="API for tracking Amazon Best Sellers Rank",
    version="1.0.0"
)

# CORS middleware (same as Flask CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(router)

# Initialize scheduler
scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Bucharest'))
scheduler.add_job(
    func=lambda: update_all_worksheets_bsr.delay(),  # Use Celery task
    trigger=CronTrigger(hour=10, minute=1, timezone=pytz.timezone('Europe/Bucharest')),
    id='daily_bsr_update',
    name='Daily BSR Update at 10:01 AM Bucharest time',
    replace_existing=True
)

# Make scheduler available to routes
app.state.scheduler = scheduler


@app.on_event("startup")
async def startup_event():
    """Start scheduler on application startup"""
    try:
        scheduler.start()
        logger.info("Scheduler started successfully")
        logger.info("Daily BSR update scheduled for 10:01 AM Bucharest time")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler and browser pool on application shutdown"""
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()
    
    # Cleanup browser pool
    from app.services.browser_pool import cleanup_browser_pool
    await cleanup_browser_pool()
    logger.info("Browser pool cleaned up")


if __name__ == "__main__":
    import uvicorn
    import config
    
    uvicorn.run(
        "app.main:app",
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        reload=(config.FLASK_ENV == 'development')
    )

