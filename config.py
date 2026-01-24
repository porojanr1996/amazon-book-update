

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

# Amazon Scraping Configuration (Production-ready settings)
AMAZON_DELAY_BETWEEN_REQUESTS = float(os.getenv('AMAZON_DELAY_BETWEEN_REQUESTS', '45'))  # Base delay
AMAZON_DELAY_MIN = float(os.getenv('AMAZON_DELAY_MIN', '45'))  # Min delay (seconds) - increased for stealth
AMAZON_DELAY_MAX = float(os.getenv('AMAZON_DELAY_MAX', '120'))  # Max delay (seconds) - increased for stealth
AMAZON_BACKOFF_ON_500 = float(os.getenv('AMAZON_BACKOFF_ON_500', '60'))  # Initial backoff on 500 error (seconds)
AMAZON_RETRY_ATTEMPTS = int(os.getenv('AMAZON_RETRY_ATTEMPTS', '1'))  # Reduced - no aggressive retries
AMAZON_MAX_WORKERS = int(os.getenv('AMAZON_MAX_WORKERS', '1'))  # Single worker - no parallel scraping
AMAZON_PLAYWRIGHT_DELAY = float(os.getenv('AMAZON_PLAYWRIGHT_DELAY', '45'))  # Delay before using Playwright (seconds)
AMAZON_SKIP_BLOCKED = os.getenv('AMAZON_SKIP_BLOCKED', 'true').lower() == 'true'  # Skip blocked books and continue
AMAZON_SKIP_ON_CAPTCHA = os.getenv('AMAZON_SKIP_ON_CAPTCHA', 'true').lower() == 'true'  # Skip immediately on CAPTCHA (don't retry)
AMAZON_BROWSER_POOL_SIZE = int(os.getenv('AMAZON_BROWSER_POOL_SIZE', '1'))  # Single browser - no parallel

# Proxy Configuration (for EC2 when Amazon blocks IP)
AMAZON_PROXY = os.getenv('AMAZON_PROXY', '')  # Format: http://user:pass@host:port or http://host:port
AMAZON_USE_PROXY = os.getenv('AMAZON_USE_PROXY', 'false').lower() == 'true'  # Enable proxy for Amazon requests

# Redis/Celery Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
# Redis cache uses same URL but different DB (1) to avoid conflicts with Celery
REDIS_CACHE_URL = os.getenv('REDIS_CACHE_URL', 'redis://localhost:6379/1')

