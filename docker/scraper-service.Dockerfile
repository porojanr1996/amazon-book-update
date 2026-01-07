FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install playwright && playwright install chromium

# Copy requirements
COPY services/scraper-service/requirements.txt .
COPY shared/config/__init__.py shared/config/
COPY shared/models/ shared/models/
COPY shared/utils/ shared/utils/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/scraper-service/ .
COPY amazon_scraper.py .
COPY app/services/playwright_scraper.py app/services/
COPY app/services/browser_pool.py app/services/
COPY app/services/amazon_scraper_tiered.py app/services/

# Expose port
EXPOSE 8002

# Run service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]

