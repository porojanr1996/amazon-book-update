"""
Celery app for worker service
"""
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from celery import Celery
from shared.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, REDIS_CACHE_URL
from shared.utils.logger import setup_logger

# Setup logger
logger = setup_logger('worker-service')

# Create Celery app
celery_app = Celery(
    'worker-service',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Bucharest',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Import tasks to register them with Celery
# This must be done after celery_app is created
# Use absolute import since we're running from worker-service directory
import tasks  # Import tasks module to register tasks

logger.info("Celery app initialized")

