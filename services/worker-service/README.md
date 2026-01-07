# Worker Service

Microserviciu pentru background jobs (Celery workers).

## Responsabilități

- Background jobs (Celery workers)
- BSR updates scheduled
- Cover extraction jobs
- Job status tracking

## Tasks

- `bsr.update_worksheet` - Update BSR pentru un worksheet
- `covers.extract_all` - Extragere covers pentru toate cărțile

## Rulare

```bash
cd services/worker-service
celery -A celery_app worker --loglevel=info
```

## Logging

Logs în `logs/worker-service.log` cu format JSON structurat.

## Dependențe

- Redis (pentru Celery broker și backend)
- sheets-service (pentru operațiuni Google Sheets)
- scraper-service (pentru scraping)

