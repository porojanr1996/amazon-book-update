FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/worker-service/requirements.txt .
COPY shared/config/__init__.py shared/config/
COPY shared/models/ shared/models/
COPY shared/utils/ shared/utils/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/worker-service/ .

# Expose port (for health checks)
EXPOSE 8003

# Run Celery worker
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]

