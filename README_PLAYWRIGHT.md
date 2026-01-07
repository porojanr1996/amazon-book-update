# Playwright Browser Pool Setup

## Overview

Selenium/undetected-chromedriver has been replaced with Playwright for better performance and reliability. The system uses a browser pool (1-3 browsers) that reuses contexts instead of spawning new ones.

## Installation

```bash
# Install Playwright Python package
pip install playwright

# Install Chromium browser
playwright install chromium

# Or install all browsers
playwright install
```

## Features

### Browser Pool
- **Pool Size**: Configurable (1-3 browsers, default: 2)
- **Context Reuse**: Contexts are reused instead of creating new ones
- **Thread-Safe**: Lock-based synchronization for concurrent access
- **Automatic Cleanup**: Proper cleanup on shutdown

### `fetch_page(url) -> html` Function
- **Location**: `app/services/browser_pool.py`
- **Retries**: Configurable (default: 3)
- **Timeouts**: Configurable (default: 30 seconds)
- **Error Handling**: Exponential backoff on retries
- **CAPTCHA Detection**: Automatically detects blocked pages

## Usage

### Basic Usage

```python
from app.services.browser_pool import fetch_page

# Async usage
html = await fetch_page("https://www.amazon.com/dp/B07QJD3B7S/")
```

### Synchronous Wrapper (for non-async code)

```python
from app.services.playwright_scraper import extract_bsr_with_playwright_sync

bsr = extract_bsr_with_playwright_sync("https://www.amazon.com/dp/B07QJD3B7S/")
```

### Direct Browser Pool Access

```python
from app.services.browser_pool import get_browser_pool

pool = get_browser_pool(pool_size=2, headless=True)
await pool.initialize()

html = await pool.fetch_page(url, timeout=30000, retries=3)
```

## Configuration

### Environment Variables

```bash
# Browser pool size (1-3)
BROWSER_POOL_SIZE=2

# Headless mode (true/false)
BROWSER_HEADLESS=true
```

### Code Configuration

```python
from app.services.browser_pool import BrowserPool

pool = BrowserPool(
    pool_size=2,      # Number of browsers (1-3)
    headless=True     # Run in headless mode
)
```

## Benefits Over Selenium

1. **Performance**: Faster page loads and better resource management
2. **Reliability**: Better handling of modern web pages
3. **Maintenance**: No ChromeDriver version management
4. **Pooling**: Reuses browser contexts for efficiency
5. **Modern**: Built for modern web applications

## Migration Notes

- All `use_selenium` parameters replaced with `use_playwright`
- All `use_undetected` parameters replaced with `use_playwright`
- Selenium methods deprecated but kept for backward compatibility
- Browser pool automatically initializes on first use
- Cleanup happens automatically on application shutdown

## Error Handling

The browser pool includes:
- **Retries**: Automatic retry with exponential backoff
- **Timeouts**: Configurable per-request timeouts
- **CAPTCHA Detection**: Detects and reports blocked pages
- **Cleanup**: Proper resource cleanup on errors

## Monitoring

Check browser pool status:
```python
from app.services.browser_pool import get_browser_pool

pool = get_browser_pool()
print(f"Initialized: {pool._initialized}")
print(f"Browsers: {len(pool.browsers)}")
print(f"Contexts: {len(pool.contexts)}")
```

