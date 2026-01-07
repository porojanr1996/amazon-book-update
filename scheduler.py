"""
Scheduler for daily BSR scraping
Runs the scraper daily at the specified time
"""
import schedule
import time
import logging
from datetime import datetime
from daily_scraper import run_daily_scrape
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def job():
    """Job function to run daily scrape"""
    logger.info("Scheduled job triggered")
    try:
        run_daily_scrape()
    except Exception as e:
        logger.error(f"Error in scheduled job: {e}", exc_info=True)


def run_scheduler():
    """Run the scheduler"""
    # Schedule the job
    schedule_time = config.SCHEDULE_TIME
    schedule.every().day.at(schedule_time).do(job)
    
    logger.info(f"Scheduler started. Will run daily at {schedule_time} ({config.SCHEDULE_TIMEZONE})")
    logger.info("Press Ctrl+C to stop")
    
    # Run immediately on startup (optional, comment out if not needed)
    # logger.info("Running initial scrape...")
    # run_daily_scrape()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == '__main__':
    try:
        run_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)

