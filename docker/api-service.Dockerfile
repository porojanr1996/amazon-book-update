FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/api-service/requirements.txt .
COPY shared/config/__init__.py shared/config/
COPY shared/models/ shared/models/
COPY shared/utils/ shared/utils/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/api-service/ .
COPY templates/ templates/
COPY static/ static/

# Expose port
EXPOSE 5001

# Run service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]

