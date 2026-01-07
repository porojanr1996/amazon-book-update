import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', 'credentials.json')
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '')

# Website Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5001))

# Scheduler Configuration
SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '10:00')
SCHEDULE_TIMEZONE = timezone(os.getenv('SCHEDULE_TIMEZONE', 'Europe/Bucharest'))

# Amazon Scraping Configuration
AMAZON_DELAY_BETWEEN_REQUESTS = float(os.getenv('AMAZON_DELAY_BETWEEN_REQUESTS', '2'))
AMAZON_RETRY_ATTEMPTS = int(os.getenv('AMAZON_RETRY_ATTEMPTS', '3'))
AMAZON_MAX_WORKERS = int(os.getenv('AMAZON_MAX_WORKERS', '1'))


# Redis/Celery Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
# Redis cache uses same URL but different DB (1) to avoid conflicts with Celery
REDIS_CACHE_URL = os.getenv('REDIS_CACHE_URL', 'redis://localhost:6379/1')
