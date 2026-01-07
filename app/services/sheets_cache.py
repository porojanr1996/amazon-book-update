"""
Google Sheets metadata cache
Caches worksheet structure to minimize read operations
Uses Redis for distributed caching
"""
import logging
import json
from typing import List, Optional
from dataclasses import dataclass, asdict

from app.services.redis_cache import get_or_set, get_cache, set_cache, delete_cache

logger = logging.getLogger(__name__)

# Cache TTL: 5 minutes (metadata doesn't change often)
METADATA_CACHE_TTL = 300


@dataclass
class WorksheetMetadata:
    """Cached worksheet metadata"""
    worksheet_name: str
    max_rows: int
    max_cols: int
    headers: List[str]
    avg_col: Optional[int] = None  # Column index (1-based) for average


def get_metadata_cache_key(worksheet_name: str) -> str:
    """Get Redis key for worksheet metadata"""
    return f"metadata:{worksheet_name}"


def get_metadata(worksheet_name: str) -> Optional[WorksheetMetadata]:
    """Get cached metadata if valid"""
    cache_key = get_metadata_cache_key(worksheet_name)
    cached_data = get_cache(cache_key)
    
    if cached_data:
        try:
            if isinstance(cached_data, dict):
                return WorksheetMetadata(**cached_data)
            elif isinstance(cached_data, str):
                return WorksheetMetadata(**json.loads(cached_data))
        except (TypeError, KeyError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to deserialize metadata for {worksheet_name}: {e}")
            delete_cache(cache_key)
    
    return None


def set_metadata(worksheet_name: str, metadata: WorksheetMetadata):
    """Cache metadata"""
    cache_key = get_metadata_cache_key(worksheet_name)
    # Convert dataclass to dict for JSON serialization
    metadata_dict = asdict(metadata)
    set_cache(cache_key, metadata_dict, METADATA_CACHE_TTL)


def invalidate_metadata(worksheet_name: Optional[str] = None):
    """Invalidate metadata cache for a worksheet or all worksheets"""
    if worksheet_name:
        cache_key = get_metadata_cache_key(worksheet_name)
        delete_cache(cache_key)
        logger.debug(f"Invalidated metadata cache for worksheet: {worksheet_name}")
    else:
        # Delete all metadata cache keys
        from app.services.redis_cache import delete_cache_pattern
        delete_cache_pattern("metadata:*")
        logger.debug("Invalidated all worksheet metadata caches")


def clear_metadata_cache():
    """Clear all metadata caches"""
    from app.services.redis_cache import delete_cache_pattern
    delete_cache_pattern("metadata:*")
    logger.info("Cleared all worksheet metadata caches")


# Backward compatibility wrapper
class SheetsMetadataCache:
    """Wrapper for backward compatibility"""
    
    def get(self, worksheet_name: str) -> Optional[WorksheetMetadata]:
        return get_metadata(worksheet_name)
    
    def set(self, worksheet_name: str, metadata: WorksheetMetadata):
        set_metadata(worksheet_name, metadata)
    
    def invalidate(self, worksheet_name: Optional[str] = None):
        invalidate_metadata(worksheet_name)
    
    def clear(self):
        clear_metadata_cache()


# Global cache instance (for backward compatibility)
_metadata_cache = SheetsMetadataCache()


def get_metadata_cache() -> SheetsMetadataCache:
    """Get global metadata cache instance"""
    return _metadata_cache

