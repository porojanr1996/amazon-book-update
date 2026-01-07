# Microservicii - Documentație Completă

## Overview

Proiectul a fost reorganizat în microservicii pentru:
- ✅ Ușurință de întreținere
- ✅ Debugging și monitoring separat
- ✅ Scalare independentă
- ✅ Deployment independent

## Structura Proiectului

```
books-reporting/
├── services/              # Microservicii
│   ├── sheets-service/    # Google Sheets operations
│   ├── scraper-service/   # Amazon scraping
│   ├── api-service/       # Web API
│   └── worker-service/    # Background jobs
├── shared/                # Cod comun
│   ├── config/            # Configurație
│   ├── models/            # Pydantic models
│   └── utils/             # Utilities
├── docker/                # Docker configs
├── scripts/               # Deployment scripts
└── docs/                  # Documentație
```

## Quick Start

### Development (Local)

```bash
# Start all services
./scripts/start_all_services.sh

# Sau manual:
cd services/sheets-service && python main.py &
cd services/scraper-service && python main.py &
cd services/api-service && python main.py &
cd services/worker-service && celery -A celery_app worker &
```

### Production (Docker)

```bash
docker-compose -f docker/docker-compose.yml up -d
```

## Servicii

### 1. Sheets Service (Port 8001)

**Responsabilități:**
- Operațiuni Google Sheets
- Batch updates optimizate
- Metadata caching

**Endpoints:**
- `GET /health` - Health check
- `GET /api/worksheets` - Lista worksheets
- `GET /api/books?worksheet=...` - Lista cărților
- `GET /api/bsr-history?worksheet=...` - Istoric BSR
- `POST /api/update-bsr` - Actualizare BSR
- `POST /api/calculate-average` - Calculare medie

**Logs:** `logs/sheets-service.log`

### 2. Scraper Service (Port 8002)

**Responsabilități:**
- Extragere BSR de pe Amazon
- Extragere cover images
- Tiered scraping strategy

**Endpoints:**
- `GET /health` - Health check
- `POST /api/extract-bsr` - Extragere BSR
- `POST /api/extract-cover` - Extragere cover

**Logs:** `logs/scraper-service.log`

### 3. API Service (Port 5001)

**Responsabilități:**
- Web API pentru frontend
- Chart data processing
- Rankings aggregation

**Endpoints:**
- `GET /health` - Health check
- `GET /api/rankings` - Rankings
- `GET /api/chart-data` - Chart data
- `POST /api/trigger-bsr-update` - Trigger BSR update

**Logs:** `logs/api-service.log`

### 4. Worker Service (Port 8003)

**Responsabilități:**
- Background jobs (Celery)
- BSR updates scheduled
- Cover extraction jobs

**Tasks:**
- `bsr.update_worksheet` - Update BSR pentru un worksheet
- `covers.extract_all` - Extragere covers pentru toate cărțile

**Logs:** `logs/worker-service.log`

## Comunicare între Servicii

### Development
- Serviciile comunică prin HTTP pe `localhost`
- Configurare în `shared/config/__init__.py`

### Production
- Serviciile comunică prin numele containerelor Docker
- Configurare în `docker-compose.yml`

## Monitoring

### Health Checks
Fiecare serviciu expune `/health` endpoint:
```bash
curl http://localhost:8001/health  # sheets-service
curl http://localhost:8002/health  # scraper-service
curl http://localhost:5001/health  # api-service
```

### Logs
Logs structurate în JSON pentru fiecare serviciu:
- `logs/sheets-service.log`
- `logs/scraper-service.log`
- `logs/api-service.log`
- `logs/worker-service.log`

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

## Beneficii

1. **Separare responsabilități** - Fiecare serviciu are un scop clar
2. **Debugging ușor** - Logs separate, erori izolate
3. **Scalare independentă** - Poți scala fiecare serviciu separat
4. **Deployment independent** - Poți deploya servicii fără să afectezi altele
5. **Testare izolată** - Poți testa fiecare serviciu separat

## Next Steps

1. Completează migrarea tuturor serviciilor
2. Adaugă monitoring (Prometheus, Grafana)
3. Adaugă tracing (Jaeger, Zipkin)
4. Creează CI/CD pipelines
5. Documentează API-urile (OpenAPI/Swagger)

