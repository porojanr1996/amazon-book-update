# Migration Guide: Production-Ready Refactored Scraper

## Overview

The refactored scraper (`browser_pool_refactored.py` and `playwright_scraper_refactored.py`) implements all production-ready improvements:

✅ **CAPTCHA Detection**: Immediate abort, no retries, marks BSR as None with reason="captcha"
✅ **Single Browser**: Pool size = 1, no parallel scraping
✅ **Increased Delays**: Random 45-120 seconds between products
✅ **Exponential Backoff**: 1 min → 3 min → 10 min for HTTP 500/503
✅ **Better Stealth**: Persistent session, realistic browser fingerprint
✅ **Smart Retry Logic**: Only network errors, never retry CAPTCHA
✅ **Metrics Tracking**: Tracks success rate, CAPTCHA rate, retry rate, scrape times
✅ **Low Memory**: Single browser instance, optimized for small EC2

## Key Changes

### 1. CAPTCHA Handling
- **Before**: Retried with multiple methods, tried to extract BSR even with CAPTCHA
- **After**: Immediate abort, returns `(None, "captcha")`, no retries

### 2. Concurrency
- **Before**: Pool size 2-3, parallel scraping
- **After**: Single browser, sequential scraping only

### 3. Delays
- **Before**: 25-75 seconds
- **After**: 45-120 seconds (configurable via `AMAZON_DELAY_MIN`/`AMAZON_DELAY_MAX`)

### 4. Error Handling
- **Before**: Retried all errors
- **After**: Only network errors (timeout, connection reset) are retried; CAPTCHA aborts immediately

### 5. Metrics
- **New**: Tracks success rate, CAPTCHA rate, retry rate, average scrape time

## Migration Steps

### Step 1: Update Imports

Replace in `amazon_scraper.py` or wherever you use Playwright:

```python
# OLD
from app.services.playwright_scraper import extract_bsr_with_playwright_sync
from app.services.browser_pool import fetch_page

# NEW
from app.services.playwright_scraper_refactored import extract_bsr_with_playwright_sync
from app.services.browser_pool_refactored import fetch_page, CaptchaDetected
```

### Step 2: Handle CAPTCHA Properly

```python
# OLD
bsr = extract_bsr_with_playwright_sync(url)
if bsr:
    # Update BSR
else:
    # Try other methods...

# NEW
bsr = extract_bsr_with_playwright_sync(url)
if bsr:
    # Update BSR
else:
    # BSR is None - could be CAPTCHA or other error
    # Check metrics to see CAPTCHA rate
    from app.services.scraper_metrics import get_metrics
    metrics = get_metrics()
    stats = metrics.get_stats()
    if stats['captcha_rate'] > 0.5:  # More than 50% CAPTCHA
        logger.warning("High CAPTCHA rate detected - consider using proxy or residential IP")
```

### Step 3: Update Configuration

Set in `.env` or environment variables:

```bash
AMAZON_DELAY_MIN=45
AMAZON_DELAY_MAX=120
AMAZON_BROWSER_POOL_SIZE=1
AMAZON_SKIP_ON_CAPTCHA=true
```

### Step 4: Monitor Metrics

```python
from app.services.scraper_metrics import get_metrics

metrics = get_metrics()
stats = metrics.get_stats()
metrics.log_stats()  # Logs all metrics

# Access individual metrics:
print(f"Success Rate: {stats['success_rate']:.1%}")
print(f"CAPTCHA Rate: {stats['captcha_rate']:.1%}")
print(f"Avg Scrape Time: {stats['avg_scrape_time']:.2f}s")
```

## Usage Example

```python
from app.services.playwright_scraper_refactored import extract_bsr_with_playwright_sync
from app.services.scraper_metrics import get_metrics

# Extract BSR
bsr = extract_bsr_with_playwright_sync(amazon_url)

if bsr:
    print(f"✅ BSR extracted: #{bsr:,}")
    # Update Google Sheets
else:
    print("❌ BSR extraction failed (CAPTCHA or error)")
    # Check metrics
    metrics = get_metrics()
    stats = metrics.get_stats()
    print(f"CAPTCHA Rate: {stats['captcha_rate']:.1%}")

# Log metrics periodically
metrics.log_stats()
```

## Performance Expectations

- **Memory Usage**: ~200-300MB (single browser)
- **Scrape Time**: 45-120s delay + 5-10s page load = ~50-130s per product
- **Success Rate**: 60-80% (depends on IP reputation)
- **CAPTCHA Rate**: 20-40% (on EC2, lower with residential IP/proxy)

## Troubleshooting

### High CAPTCHA Rate (>50%)
- Use residential proxy (ScraperAPI, Bright Data)
- Increase delays (set `AMAZON_DELAY_MAX=180`)
- Use residential IP instead of EC2

### Memory Issues
- Already optimized for single browser
- Check for memory leaks in other parts of code
- Restart service periodically

### Slow Scraping
- Expected: 45-120s delays are intentional for stealth
- Consider running during off-peak hours
- Use multiple EC2 instances with different IPs

## Rollback

If you need to rollback to old version:

```python
# Just use old imports
from app.services.playwright_scraper import extract_bsr_with_playwright_sync
from app.services.browser_pool import fetch_page
```

Both versions can coexist - just change imports.

