"""
Cache service for chart data and cover images
Uses Redis for distributed caching
"""
import logging
from typing import Optional, Dict, Any

from app.services.redis_cache import get_cache, set_cache, delete_cache_pattern, clear_all_cache

logger = logging.getLogger(__name__)

# Cache TTLs
CHART_CACHE_TTL = 300  # 5 minutes
COVER_CACHE_TTL = 86400  # 24 hours


def get_cached_chart_data(time_range: str, worksheet: str = '') -> Optional[Dict[str, Any]]:
    """Get cached chart data if available and not expired"""
    cache_key = f"chart:{time_range}:{worksheet}"
    return get_cache(cache_key)


def set_cached_chart_data(time_range: str, worksheet: str = '', data: Optional[Dict[str, Any]] = None):
    """Cache chart data"""
    cache_key = f"chart:{time_range}:{worksheet}"
    set_cache(cache_key, data, CHART_CACHE_TTL)


def invalidate_chart_cache(worksheet_name: Optional[str] = None):
    """Invalidate chart cache for a specific worksheet or all worksheets"""
    if worksheet_name:
        # Delete all chart cache keys for this worksheet
        pattern = f"chart:*:{worksheet_name}"
        logger.info(f"Invalidating chart cache with pattern: {pattern}")
        delete_cache_pattern(pattern)
        logger.info(f"✓ Chart cache invalidated for worksheet: {worksheet_name}")
    else:
        # Delete all chart cache keys
        pattern = "chart:*"
        logger.info(f"Invalidating all chart cache with pattern: {pattern}")
        delete_cache_pattern(pattern)
        logger.info("✓ Chart cache invalidated for all worksheets.")


def get_cached_cover(amazon_link: str) -> Optional[str]:
    """Get cached cover image if available and not expired"""
    cache_key = f"cover:{amazon_link}"
    return get_cache(cache_key)


def set_cached_cover(amazon_link: str, cover_url: Optional[str]):
    """Cache cover image"""
    cache_key = f"cover:{amazon_link}"
    set_cache(cache_key, cover_url, COVER_CACHE_TTL)


def clear_all_caches():
    """Clear all caches"""
    clear_all_cache()
    logger.info("All caches cleared")
