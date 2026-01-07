"""
ETag and Last-Modified header service
Generates ETags and tracks Last-Modified timestamps for cache validation
"""
import hashlib
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from app.services.redis_cache import get_cache, set_cache

logger = logging.getLogger(__name__)

# Cache TTL for Last-Modified timestamps (24 hours)
LAST_MODIFIED_TTL = 86400


def generate_etag(data: Any) -> str:
    """
    Generate ETag from data content
    
    Args:
        data: Data to generate ETag for
        
    Returns:
        ETag string (weak ETag with 'W/' prefix)
    """
    try:
        # Serialize data to JSON for hashing
        if isinstance(data, (dict, list)):
            json_str = json.dumps(data, sort_keys=True, default=str)
        else:
            json_str = str(data)
        
        # Generate MD5 hash
        hash_obj = hashlib.md5(json_str.encode('utf-8'))
        etag = hash_obj.hexdigest()
        
        # Return weak ETag (W/ prefix) for better compatibility
        return f'W/"{etag}"'
    except Exception as e:
        logger.error(f"Error generating ETag: {e}")
        # Fallback: use timestamp-based ETag
        return f'W/"{int(datetime.now().timestamp())}"'


def get_last_modified(worksheet_name: str, data_type: str = 'chart') -> Optional[str]:
    """
    Get Last-Modified timestamp for a resource
    
    Args:
        worksheet_name: Worksheet name
        data_type: Type of data ('chart' or 'rankings')
        
    Returns:
        Last-Modified timestamp as HTTP date string, or None
    """
    cache_key = f"last_modified:{data_type}:{worksheet_name}"
    timestamp = get_cache(cache_key)
    
    if timestamp:
        try:
            # Convert timestamp to HTTP date format
            dt = datetime.fromtimestamp(float(timestamp))
            return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
        except Exception as e:
            logger.warning(f"Error formatting Last-Modified: {e}")
    
    return None


def set_last_modified(worksheet_name: str, data_type: str = 'chart', timestamp: Optional[float] = None):
    """
    Set Last-Modified timestamp for a resource
    
    Args:
        worksheet_name: Worksheet name
        data_type: Type of data ('chart' or 'rankings')
        timestamp: Unix timestamp (defaults to now)
    """
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    
    cache_key = f"last_modified:{data_type}:{worksheet_name}"
    set_cache(cache_key, timestamp, LAST_MODIFIED_TTL)
    logger.debug(f"Set Last-Modified for {data_type}:{worksheet_name} = {timestamp}")


def invalidate_last_modified(worksheet_name: str, data_type: Optional[str] = None):
    """
    Invalidate Last-Modified timestamp
    
    Args:
        worksheet_name: Worksheet name
        data_type: Type of data ('chart' or 'rankings'), or None for all types
    """
    from app.services.redis_cache import delete_cache
    
    if data_type:
        cache_key = f"last_modified:{data_type}:{worksheet_name}"
        delete_cache(cache_key)
    else:
        # Invalidate both chart and rankings
        for dt in ['chart', 'rankings']:
            cache_key = f"last_modified:{dt}:{worksheet_name}"
            delete_cache(cache_key)
    
    logger.debug(f"Invalidated Last-Modified for {data_type or 'all'}:{worksheet_name}")


def check_if_none_match(request_etag: Optional[str], current_etag: str) -> bool:
    """
    Check if client's If-None-Match header matches current ETag
    
    Args:
        request_etag: ETag from If-None-Match header
        current_etag: Current ETag of the resource
        
    Returns:
        True if ETags match (should return 304), False otherwise
    """
    if not request_etag:
        return False
    
    # Remove quotes and W/ prefix for comparison
    def normalize_etag(etag: str) -> str:
        etag = etag.strip()
        if etag.startswith('W/"') and etag.endswith('"'):
            return etag[3:-1]
        elif etag.startswith('"') and etag.endswith('"'):
            return etag[1:-1]
        return etag
    
    normalized_request = normalize_etag(request_etag)
    normalized_current = normalize_etag(current_etag)
    
    return normalized_request == normalized_current


def check_if_modified_since(request_date: Optional[str], last_modified: Optional[str]) -> bool:
    """
    Check if resource was modified since request date
    
    Args:
        request_date: Date from If-Modified-Since header
        last_modified: Last-Modified date of the resource
        
    Returns:
        True if resource was modified (should return 200), False if not modified
    """
    if not request_date or not last_modified:
        return True  # If either is missing, return full response
    
    try:
        # Parse HTTP date format: "Wed, 21 Oct 2015 07:28:00 GMT"
        request_dt = datetime.strptime(request_date, '%a, %d %b %Y %H:%M:%S %Z')
        last_modified_dt = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
        
        # Resource was modified if last_modified > request_date
        return last_modified_dt > request_dt
    except Exception as e:
        logger.warning(f"Error parsing dates for If-Modified-Since: {e}")
        return True  # On error, return full response

