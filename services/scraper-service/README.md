# Scraper Service

Microserviciu pentru extragerea datelor de pe Amazon (BSR și cover images).

## Responsabilități

- Extragere BSR de pe Amazon
- Extragere cover images
- Tiered scraping strategy (httpx → Playwright → blocked)
- Rate limiting și retry logic

## Endpoints

- `GET /health` - Health check
- `POST /api/extract-bsr` - Extragere BSR pentru o carte
- `POST /api/extract-cover` - Extragere cover image pentru o carte
- `POST /api/extract-batch` - Extragere BSR pentru multiple cărți

## Rulare

```bash
cd services/scraper-service
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## Logging

Logs în `logs/scraper-service.log` cu format JSON structurat.
Scraping failures în `amazon_scraping_failures.jsonl`.

## Dependențe

- Playwright pentru browser automation
- httpx pentru HTTP requests
- Redis pentru caching

