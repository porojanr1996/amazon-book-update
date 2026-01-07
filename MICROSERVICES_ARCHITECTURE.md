# Arhitectură Microservicii

## Overview

Proiectul este împărțit în microservicii separate pentru ușurință de întreținere, debugging și scalare.

## Structura Microserviciilor

```
books-reporting/
├── services/
│   ├── sheets-service/          # Google Sheets operations
│   ├── scraper-service/         # Amazon scraping (BSR + covers)
│   ├── api-service/             # Web API (FastAPI)
│   ├── worker-service/          # Background jobs (Celery)
│   └── cache-service/            # Redis caching (shared library)
├── shared/                      # Cod comun
│   ├── models/                  # Pydantic models
│   ├── utils/                   # Utilities comune
│   └── config/                  # Configurație comună
├── frontend/                    # Static files
├── docker/                      # Docker configs
├── scripts/                     # Deployment scripts
└── docs/                        # Documentație
```

## Microservicii

### 1. sheets-service
**Responsabilități:**
- Citire/scriere date din Google Sheets
- Gestionare worksheets
- Batch updates optimizate
- Metadata caching

**Interfață:**
- REST API: `http://sheets-service:8001`
- Health: `GET /health`
- Endpoints: `/api/worksheets`, `/api/books`, `/api/update-bsr`, etc.

**Logging:**
- `services/sheets-service/logs/` - Logs separate
- Structured logging cu correlation IDs

### 2. scraper-service
**Responsabilități:**
- Extragere BSR de pe Amazon
- Extragere cover images
- Tiered scraping strategy (httpx → Playwright → blocked)
- Rate limiting și retry logic

**Interfață:**
- REST API: `http://scraper-service:8002`
- Health: `GET /health`
- Endpoints: `/api/extract-bsr`, `/api/extract-cover`, etc.

**Logging:**
- `services/scraper-service/logs/` - Logs separate
- Scraping failures în `amazon_scraping_failures.jsonl`

### 3. api-service
**Responsabilități:**
- Web API pentru frontend
- Chart data processing
- Rankings aggregation
- ETag și caching headers

**Interfață:**
- REST API: `http://api-service:5001`
- Health: `GET /health`
- Endpoints: `/api/rankings`, `/api/chart-data`, etc.

**Logging:**
- `services/api-service/logs/` - Logs separate
- Request/response logging

### 4. worker-service
**Responsabilități:**
- Background jobs (Celery workers)
- BSR updates scheduled
- Cover extraction jobs
- Job status tracking

**Interfață:**
- Celery: `redis://redis:6379/0`
- Health: `GET /health` (HTTP endpoint pentru monitoring)
- Tasks: `bsr.update_worksheet`, `covers.extract_all`, etc.

**Logging:**
- `services/worker-service/logs/` - Logs separate
- Job progress și errors

### 5. cache-service (shared library)
**Responsabilități:**
- Redis caching operations
- Cache invalidation
- ETag generation
- Last-Modified tracking

**Interfață:**
- Library importat în alte servicii
- Redis: `redis://redis:6379/1`

## Comunicare între Servicii

### API Calls
- `api-service` → `sheets-service` (pentru date)
- `api-service` → `scraper-service` (pentru scraping on-demand)
- `worker-service` → `sheets-service` (pentru updates)
- `worker-service` → `scraper-service` (pentru scraping)

### Message Queue
- Redis pentru Celery tasks
- Tasks enqueued de `api-service`, procesate de `worker-service`

### Shared State
- Redis pentru caching
- Google Sheets ca source of truth pentru date

## Deployment

### Development
```bash
# Start all services
docker-compose up

# Start individual service
cd services/api-service && python -m uvicorn main:app --reload
```

### Production
- Fiecare serviciu rulează în container Docker separat
- Orchestrare cu docker-compose sau Kubernetes
- Load balancing pentru `api-service` și `scraper-service`

## Monitoring și Debugging

### Health Checks
- Fiecare serviciu expune `/health` endpoint
- Verificare periodică cu monitoring tools

### Logging
- Logs separate pentru fiecare serviciu
- Structured logging (JSON format)
- Correlation IDs pentru tracing requests

### Metrics
- Request counts și latencies
- Error rates
- Scraping success rates
- Cache hit rates

## Beneficii

1. **Separare responsabilități** - Fiecare serviciu are un scop clar
2. **Scalare independentă** - Poți scala fiecare serviciu separat
3. **Debugging ușor** - Logs separate, erori izolate
4. **Deployment independent** - Poți deploya servicii fără să afectezi altele
5. **Testare izolată** - Poți testa fiecare serviciu separat

