# Tiered Amazon Scraping Strategy

## Overview

A three-tier scraping strategy for Amazon pages that maximizes success rate while minimizing resource usage.

## Architecture

### Tier 1: httpx/requests with Aggressive Caching
- **Technology**: httpx (HTTP/2 support) with realistic headers
- **Caching**: Aggressive caching (1 hour TTL by default)
- **Speed**: Fastest method
- **Use Case**: Normal Amazon pages

### Tier 2: Playwright Fallback
- **Technology**: Playwright browser pool
- **Trigger**: When Tier 1 detects robot check/CAPTCHA
- **Speed**: Slower but more reliable
- **Use Case**: JavaScript-rendered pages or blocked requests

### Tier 3: Mark as Blocked with Exponential Backoff
- **Action**: Mark book URL as blocked
- **Retry**: Exponential backoff (1h, 2h, 4h, 8h, 24h max)
- **Logging**: Structured failure logs
- **Use Case**: All tiers failed

## Robot Detection

The `AmazonRobotDetector` class reliably detects robot check pages using:

### Indicators of Robot Pages:
- `robot.*check`
- `captcha`
- `verify.*you.*are.*human`
- `sorry.*we.*just.*need.*verify`
- `enter.*characters.*you.*see`
- `access.*denied`
- `blocked.*request`
- `too.*many.*requests`
- `rate.*limit`

### Indicators of Normal Pages:
- `product.*details`
- `add.*to.*cart`
- `buy.*now`
- `amazon.*best.*seller`
- `customer.*reviews`
- `product.*information`

## Structured Logging

All failures are logged to `amazon_scraping_failures.jsonl` with:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "url": "https://www.amazon.com/dp/B07QJD3B7S/",
  "tier": 1,
  "failure_type": "blocked",
  "error_message": "robot_indicator: captcha",
  "page_length": 5000,
  "page_snippet": "...",
  "retry_after": "2024-01-15T11:30:00"
}
```

## Usage

### Enable Tiered Scraping

```python
from amazon_scraper import AmazonScraper

# Enable tiered scraping (default: True)
scraper = AmazonScraper(use_tiered=True)

# Extract BSR
bsr = scraper.extract_bsr("https://www.amazon.com/dp/B07QJD3B7S/")

# Extract cover image
cover = scraper.extract_cover_image("https://www.amazon.com/dp/B07QJD3B7S/")
```

### Direct Tiered Scraper Access

```python
from app.services.amazon_scraper_tiered import get_tiered_scraper

scraper = get_tiered_scraper()
html = scraper.fetch_page("https://www.amazon.com/dp/B07QJD3B7S/")
```

## Configuration

### Cache TTL
```python
scraper = TieredAmazonScraper(cache_ttl=3600)  # 1 hour default
```

### Max Retry Delay
```python
scraper = TieredAmazonScraper(max_retry_delay=86400)  # 24 hours default
```

## Benefits

1. **Performance**: Tier 1 is fastest with caching
2. **Reliability**: Tier 2 handles JavaScript and bot detection
3. **Resilience**: Tier 3 prevents repeated failures
4. **Observability**: Structured logging for analysis
5. **Efficiency**: Aggressive caching reduces requests

## Failure Analysis

View failures:
```bash
# View all failures
cat amazon_scraping_failures.jsonl | jq '.'

# Count failures by type
cat amazon_scraping_failures.jsonl | jq -r '.failure_type' | sort | uniq -c

# Find blocked URLs
cat amazon_scraping_failures.jsonl | jq 'select(.failure_type == "blocked")'
```

## Monitoring

Check blocked books:
```python
from app.services.amazon_scraper_tiered import get_tiered_scraper

scraper = get_tiered_scraper()
print(f"Blocked books: {len(scraper.blocked_books)}")
for url, retry_after in scraper.blocked_books.items():
    print(f"{url}: retry after {retry_after}")
```

