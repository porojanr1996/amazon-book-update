# Documentație Servicii

## Overview

Proiectul este împărțit în 4 microservicii principale, fiecare cu responsabilități clare.

## 1. Sheets Service

**Port:** 8001  
**Responsabilități:** Operațiuni Google Sheets

### Endpoints

- `GET /health` - Health check
- `GET /api/worksheets` - Lista tuturor worksheets
- `GET /api/books?worksheet=...` - Lista cărților dintr-un worksheet
- `GET /api/bsr-history?worksheet=...` - Istoric BSR pentru toate cărțile
- `GET /api/avg-history?worksheet=...` - Istoric medii BSR
- `GET /api/today-row?worksheet=...` - Rândul pentru data de azi
- `POST /api/update-bsr` - Actualizare BSR pentru o carte
- `POST /api/calculate-average` - Calculare și actualizare medie BSR

### Dependențe

- Google Sheets API
- Redis (pentru caching)

### Logs

`logs/sheets-service.log`

## 2. Scraper Service

**Port:** 8002  
**Responsabilități:** Extragere date de pe Amazon

### Endpoints

- `GET /health` - Health check
- `POST /api/extract-bsr` - Extragere BSR pentru o carte
- `POST /api/extract-cover` - Extragere cover image pentru o carte
- `POST /api/extract-batch` - Extragere BSR pentru multiple cărți

### Request Models

**ExtractBSRRequest:**
```json
{
  "amazon_url": "https://www.amazon.com/dp/...",
  "use_playwright": false
}
```

**ExtractCoverRequest:**
```json
{
  "amazon_url": "https://www.amazon.com/dp/...",
  "use_playwright": true
}
```

### Dependențe

- Playwright (pentru browser automation)
- httpx (pentru HTTP requests)
- Redis (pentru caching)

### Logs

`logs/scraper-service.log`  
`amazon_scraping_failures.jsonl` (pentru failures)

## 3. API Service

**Port:** 5001  
**Responsabilități:** Web API pentru frontend

### Endpoints

- `GET /health` - Health check
- `GET /` - Dashboard page
- `GET /api/worksheets` - Lista worksheets (proxy)
- `GET /api/rankings?worksheet=...` - Rankings cu cover images
- `GET /api/chart-data?range=...&worksheet=...` - Date pentru grafic
- `POST /api/trigger-bsr-update` - Trigger BSR update
- `GET /api/jobs/{job_id}` - Status job

### Dependențe

- sheets-service
- scraper-service
- Redis (pentru caching)
- worker-service (pentru background jobs)

### Logs

`logs/api-service.log`

## 4. Worker Service

**Port:** 8003 (Celery)  
**Responsabilități:** Background jobs

### Tasks

**bsr.update_worksheet:**
- Update BSR pentru toate cărțile dintr-un worksheet
- Parametri: `worksheet_name` (str)
- Returnează: `{success_count, failure_count, total_books}`

**covers.extract_all:**
- Extragere cover images pentru toate cărțile
- Parametri: `worksheet_name` (str)
- Returnează: `{success_count, failure_count, total_books}`

### Dependențe

- Redis (pentru Celery broker și backend)
- sheets-service
- scraper-service

### Logs

`logs/worker-service.log`

## Comunicare între Servicii

### Development
- Serviciile comunică prin HTTP pe `localhost`
- Configurare în `shared/config/__init__.py`

### Production
- Serviciile comunică prin numele containerelor Docker
- Configurare în `docker-compose.yml`

## Monitoring

### Health Checks
Fiecare serviciu expune `/health` endpoint pentru monitoring.

### Logs
Logs structurate în JSON pentru fiecare serviciu, cu:
- Timestamp
- Level (INFO, WARNING, ERROR)
- Service name
- Message
- Correlation ID (pentru tracing)

### Metrics
- Request counts și latencies
- Error rates
- Scraping success rates
- Cache hit rates

## Troubleshooting

### Service nu pornește
1. Verifică logs: `tail -f logs/<service-name>.log`
2. Verifică portul: `lsof -i :<port>`
3. Verifică dependențe: Redis, Google Sheets credentials

### Service nu răspunde
1. Verifică health check: `curl http://localhost:<port>/health`
2. Verifică logs pentru erori
3. Verifică conectivitatea între servicii

### Erori de comunicare între servicii
1. Verifică variabilele de mediu: `SHEETS_SERVICE_URL`, `SCRAPER_SERVICE_URL`
2. Verifică că serviciile sunt pornite
3. Verifică firewall/network settings

