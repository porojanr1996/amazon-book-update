# API Service

Microserviciu pentru Web API-ul frontend-ului.

## Responsabilități

- Web API pentru frontend
- Chart data processing
- Rankings aggregation
- ETag și caching headers

## Endpoints

- `GET /health` - Health check
- `GET /` - Dashboard page
- `GET /api/worksheets` - Lista worksheets (proxy la sheets-service)
- `GET /api/rankings?worksheet=...` - Rankings cu cover images
- `GET /api/chart-data?range=...&worksheet=...` - Date pentru grafic
- `POST /api/trigger-bsr-update` - Trigger BSR update (enqueue job)
- `GET /api/jobs/{job_id}` - Status job
- `GET /api/scheduler-status` - Status scheduler

## Rulare

```bash
cd services/api-service
python -m uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

## Logging

Logs în `logs/api-service.log` cu format JSON structurat.

## Dependențe

- sheets-service (pentru date Google Sheets)
- scraper-service (pentru scraping on-demand)
- Redis (pentru caching)
- worker-service (pentru background jobs)

