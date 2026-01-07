#!/bin/bash
# Start Celery worker for BSR update tasks

celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --pool=prefork \
    --hostname=bsr_worker@%h

