FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/sheets-service/requirements.txt .
COPY shared/config/__init__.py shared/config/
COPY shared/models/ shared/models/
COPY shared/utils/ shared/utils/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/sheets-service/ .
COPY google_sheets_transposed.py .
COPY app/services/sheets_cache.py app/services/

# Expose port
EXPOSE 8001

# Run service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

