"""
Shared configuration for all microservices
"""
import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', 'credentials.json')
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '')

# Service Configuration
SERVICE_ENV = os.getenv('SERVICE_ENV', 'development')
SERVICE_HOST = os.getenv('SERVICE_HOST', '0.0.0.0')

# Ports for each service
SHEETS_SERVICE_PORT = int(os.getenv('SHEETS_SERVICE_PORT', '8001'))
SCRAPER_SERVICE_PORT = int(os.getenv('SCRAPER_SERVICE_PORT', '8002'))
API_SERVICE_PORT = int(os.getenv('API_SERVICE_PORT', '5001'))
WORKER_SERVICE_PORT = int(os.getenv('WORKER_SERVICE_PORT', '8003'))

# Scheduler Configuration
SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '10:00')
SCHEDULE_TIMEZONE = timezone(os.getenv('SCHEDULE_TIMEZONE', 'Europe/Bucharest'))

# Amazon Scraping Configuration
AMAZON_DELAY_BETWEEN_REQUESTS = float(os.getenv('AMAZON_DELAY_BETWEEN_REQUESTS', '8'))
AMAZON_RETRY_ATTEMPTS = int(os.getenv('AMAZON_RETRY_ATTEMPTS', '3'))
AMAZON_MAX_WORKERS = int(os.getenv('AMAZON_MAX_WORKERS', '1'))

# Redis/Celery Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
REDIS_CACHE_URL = os.getenv('REDIS_CACHE_URL', 'redis://localhost:6379/1')

# Service URLs (for inter-service communication)
SHEETS_SERVICE_URL = os.getenv('SHEETS_SERVICE_URL', f'http://localhost:{SHEETS_SERVICE_PORT}')
SCRAPER_SERVICE_URL = os.getenv('SCRAPER_SERVICE_URL', f'http://localhost:{SCRAPER_SERVICE_PORT}')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'

