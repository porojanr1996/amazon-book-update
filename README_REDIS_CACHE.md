# Redis Cache Implementation

## Overview

All in-memory caching has been replaced with Redis for distributed caching across multiple instances.

## Features

### Shared Cache Helper

The `get_or_set(key, ttl, callback)` function provides a simple interface:

```python
from app.services.redis_cache import get_or_set

# Get from cache or execute callback
value = get_or_set(
    key="my_key",
    ttl=300,  # 5 minutes
    callback=lambda: expensive_operation(),
    default=None
)
```

## Cached Data Types

### 1. Chart Data (5 minutes TTL)
- **Key Pattern**: `chart:{time_range}:{worksheet}`
- **Example**: `chart:30:Crime Fiction - US`
- **Invalidation**: After BSR updates per worksheet

### 2. Book Cover Images (24 hours TTL)
- **Key Pattern**: `cover:{amazon_link}`
- **Example**: `cover:https://www.amazon.com/dp/B07QJD3B7S/`
- **Invalidation**: Manual clear or TTL expiration

### 3. Worksheet Metadata (5 minutes TTL)
- **Key Pattern**: `metadata:{worksheet_name}`
- **Example**: `metadata:Crime Fiction - US`
- **Invalidation**: After BSR updates per worksheet

### 4. HTML Cache (1 hour TTL)
- **Key Pattern**: `html:{url}`
- **Example**: `html:https://www.amazon.com/dp/B07QJD3B7S/`
- **Invalidation**: TTL expiration

## Cache Invalidation

### After BSR Updates

When BSR is updated for a worksheet, the following caches are invalidated:

1. **Chart Cache**: All chart data for the worksheet
   ```python
   invalidate_chart_cache(worksheet_name)
   ```

2. **Metadata Cache**: Worksheet metadata
   ```python
   from app.services.sheets_cache import invalidate_metadata
   invalidate_metadata(worksheet_name)
   ```

### Manual Cache Clearing

```python
from app.services.cache_service import clear_all_caches
clear_all_caches()  # Clears all Redis cache
```

## Installation and Setup

### Install Redis (macOS)

```bash
brew install redis
```

### Start Redis Server

**Option 1: Start as a service (recommended - auto-starts on login)**
```bash
brew services start redis
```

**Option 2: Start manually**
```bash
redis-server
```

### Verify Redis is Running

```bash
redis-cli ping
# Should return: PONG
```

## Configuration

### Redis URL

Set in `.env`:
```bash
REDIS_URL=redis://localhost:6379/0  # For Celery
REDIS_CACHE_URL=redis://localhost:6379/1  # For cache (different DB)
```

### Fallback Behavior

If Redis is unavailable, the system will:
- Log warnings
- Continue without caching (no errors)
- Fall back to direct operations

**Note**: Redis is required for optimal performance. Without Redis, the app will work but caching will be disabled.

## Usage Examples

### Chart Data Caching

```python
from app.services.chart_service import get_chart_data

# Automatically cached for 5 minutes
chart_data = await get_chart_data("30", "Crime Fiction - US")
```

### Cover Image Caching

```python
from app.services.cache_service import get_cached_cover, set_cached_cover

# Get from cache
cover_url = get_cached_cover(amazon_link)

# Set in cache
set_cached_cover(amazon_link, cover_url)
```

### Metadata Caching

```python
from app.services.sheets_cache import get_metadata, set_metadata

# Get cached metadata
metadata = get_metadata(worksheet_name)

# Cache metadata
set_metadata(worksheet_name, metadata)
```

## Benefits

1. **Distributed**: Multiple app instances share the same cache
2. **Persistent**: Cache survives app restarts
3. **Scalable**: Redis handles high throughput
4. **TTL Management**: Automatic expiration
5. **Pattern Matching**: Efficient bulk invalidation

## Monitoring

Check Redis cache status:
```bash
redis-cli
> KEYS chart:*
> KEYS cover:*
> KEYS metadata:*
> TTL chart:30:Crime Fiction - US
```

## Performance

- **Cache Hit**: < 1ms (Redis lookup)
- **Cache Miss**: Normal operation time + cache write
- **Invalidation**: Pattern-based deletion (very fast)

