# Celery Background Jobs Setup

## Overview

BSR updates now use Celery + Redis for proper background job processing instead of manual threading.

## Prerequisites

1. **Redis Server** must be running:
   ```bash
   # Install Redis (macOS)
   brew install redis
   
   # Start Redis as a service (recommended - auto-starts on login)
   brew services start redis
   
   # Or start manually (temporary)
   redis-server
   
   # Or use Docker
   docker run -d -p 6379:6379 redis:7-alpine
   ```
   
   **Verify Redis is running:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

## Installation

```bash
pip install celery redis
```

## Configuration

Set Redis URL in `.env` or `config.py`:
```python
REDIS_URL = 'redis://localhost:6379/0'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

## Running

### 1. Start Redis (if not already running)
```bash
# Check if Redis is running
redis-cli ping

# If not running, start it:
brew services start redis  # macOS - starts as service
# OR
redis-server  # Manual start
```

### 2. Start Celery Worker
```bash
# Option 1: Use the script
./start_celery_worker.sh

# Option 2: Manual command
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

### 3. Start FastAPI Application
```bash
python run_fastapi.py
```

## API Usage

### Trigger BSR Update

**POST** `/api/trigger-bsr-update`

Request body:
```json
{
  "worksheet": "Crime Fiction - US"  // Optional, omit to update all
}
```

Response:
```json
{
  "status": "started",
  "message": "BSR update started for worksheet \"Crime Fiction - US\".",
  "worksheet": "Crime Fiction - US",
  "job_id": "abc123-def456-ghi789"
}
```

### Check Job Status

**GET** `/api/jobs/{job_id}`

Response (PENDING):
```json
{
  "job_id": "abc123-def456-ghi789",
  "state": "PENDING",
  "status": "Job is waiting to be processed",
  "progress": null
}
```

Response (PROGRESS):
```json
{
  "job_id": "abc123-def456-ghi789",
  "state": "PROGRESS",
  "status": "Processed 15/31 books...",
  "progress": {
    "current": 15,
    "total": 31,
    "percentage": 48.39
  },
  "worksheet": "Crime Fiction - US",
  "success_count": 12,
  "failure_count": 3
}
```

Response (SUCCESS):
```json
{
  "job_id": "abc123-def456-ghi789",
  "state": "SUCCESS",
  "status": "completed",
  "result": {
    "status": "completed",
    "worksheet": "Crime Fiction - US",
    "success_count": 28,
    "failure_count": 3,
    "total_books": 31,
    "elapsed_time": 45.23,
    "message": "BSR update completed: 28 success, 3 failures"
  },
  "progress": {
    "current": 31,
    "total": 31,
    "percentage": 100
  }
}
```

Response (FAILURE):
```json
{
  "job_id": "abc123-def456-ghi789",
  "state": "FAILURE",
  "status": "failed",
  "error": "Connection timeout",
  "traceback": "..."
}
```

## Frontend Integration

Update the frontend to poll job status:

```javascript
async function triggerBsrUpdate(worksheet) {
    const response = await fetch('/api/trigger-bsr-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ worksheet })
    });
    
    const data = await response.json();
    const jobId = data.job_id;
    
    // Poll job status
    const pollInterval = setInterval(async () => {
        const statusResponse = await fetch(`/api/jobs/${jobId}`);
        const status = await statusResponse.json();
        
        if (status.state === 'SUCCESS') {
            clearInterval(pollInterval);
            // Reload data
            loadChart();
            loadRankings();
        } else if (status.state === 'FAILURE') {
            clearInterval(pollInterval);
            // Show error
            console.error('Job failed:', status.error);
        }
        // Update UI with progress
        updateProgressBar(status.progress);
    }, 2000); // Poll every 2 seconds
}
```

## Monitoring

### Celery Flower (Optional)

Install Flower for web-based monitoring:
```bash
pip install flower
celery -A app.celery_app flower
```

Access at: http://localhost:5555

### Redis CLI

Check Redis:
```bash
redis-cli
> KEYS *
> GET celery-task-meta-{job_id}
```

## Benefits

1. **Proper Job Queue**: Jobs are persisted and can survive server restarts
2. **Progress Tracking**: Real-time progress updates
3. **Error Handling**: Better error tracking and retry capabilities
4. **Scalability**: Can run multiple workers for parallel processing
5. **Monitoring**: Built-in monitoring tools (Flower)
6. **Reliability**: Jobs are not lost if server crashes

