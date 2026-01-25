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

# Initialize scheduler (only if Celery is available)
scheduler = None
try:
    from app.tasks.bsr_tasks import update_all_worksheets_bsr
    
    # Wrapper function to ensure task is sent correctly
    def send_daily_bsr_task():
        """Wrapper to send daily BSR update task to Celery"""
        try:
            logger.info("Sending daily BSR update task to Celery...")
            result = update_all_worksheets_bsr.delay()
            logger.info(f"Daily BSR update task sent to Celery with ID: {result.id}")
            logger.info(f"Task state: {result.state}")
            return result
        except Exception as e:
            logger.error(f"Error sending daily BSR update task to Celery: {e}", exc_info=True)
            raise
    
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Bucharest'))
    scheduler.add_job(
        func=send_daily_bsr_task,  # Use wrapper function
        trigger=CronTrigger(hour=10, minute=0, timezone=pytz.timezone('Europe/Bucharest')),
        id='daily_bsr_update',
        name='Daily BSR Update at 10:00 AM Bucharest time',
        replace_existing=True
    )
    logger.info("Scheduler initialized with Celery tasks")
except Exception as e:
    logger.warning(f"Scheduler not initialized (Celery may not be available): {e}")
    scheduler = None

# Make scheduler available to routes
app.state.scheduler = scheduler


@app.on_event("startup")
async def startup_event():
    """Start scheduler on application startup"""
    if scheduler:
        try:
            scheduler.start()
            logger.info("Scheduler started successfully")
            logger.info("Daily BSR update scheduled for 10:00 AM Bucharest time")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
    else:
        logger.info("Scheduler not started (Celery not available)")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler and browser pool on application shutdown"""
    if scheduler:
        logger.info("Shutting down scheduler...")
        try:
            scheduler.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}", exc_info=True)
    
    # Cleanup browser pool
    try:
        from app.services.browser_pool import cleanup_browser_pool
        await cleanup_browser_pool()
        logger.info("Browser pool cleaned up")
    except Exception as e:
        logger.warning(f"Error cleaning up browser pool: {e}", exc_info=True)


if __name__ == "__main__":
    import uvicorn
    import config
    import os
    
    # Get root_path from environment variable (for subpath deployment)
    root_path = os.getenv('ROOT_PATH', '')
    
    uvicorn.run(
        "app.main:app",
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        reload=(config.FLASK_ENV == 'development'),
        root_path=root_path
    )

