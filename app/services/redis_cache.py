"""
Redis Cache Helper
Shared cache service using Redis for distributed caching
"""
import json
import logging
import time
from typing import Optional, Callable, Any, TypeVar
import redis
from redis.exceptions import RedisError, ConnectionError

import config

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Redis connection pool (singleton)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client singleton"""
    global _redis_client
    
    if _redis_client is None:
        try:
            # Use REDIS_CACHE_URL if available, otherwise fall back to REDIS_URL
            redis_url = getattr(config, 'REDIS_CACHE_URL', None) or getattr(config, 'REDIS_URL', 'redis://localhost:6379/1')
            _redis_client = redis.from_url(
                redis_url,
                decode_responses=True,  # Automatically decode bytes to strings
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established successfully")
        except (RedisError, ConnectionError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Falling back to in-memory cache")
            _redis_client = None
    
    return _redis_client


def get_or_set(key: str, ttl: int, callback: Callable[[], T], default: Optional[T] = None) -> Optional[T]:
    """
    Get value from cache or set it using callback
    
    Args:
        key: Cache key
        ttl: Time to live in seconds
        callback: Function to call if cache miss (returns value to cache)
        default: Default value if callback fails and cache miss
        
    Returns:
        Cached value or callback result, or default if both fail
    """
    redis_client = get_redis_client()
    
    # Try to get from Redis
    if redis_client:
        try:
            cached_value = redis_client.get(key)
            if cached_value is not None:
                try:
                    # Try to deserialize JSON
                    return json.loads(cached_value)
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, return as string
                    return cached_value
        except RedisError as e:
            logger.warning(f"Redis get error for key {key}: {e}")
    
    # Cache miss - call callback
    try:
        value = callback()
        if value is not None:
            set_cache(key, value, ttl)
        return value
    except Exception as e:
        logger.error(f"Callback error for key {key}: {e}")
        return default


def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    redis_client = get_redis_client()
    
    if not redis_client:
        return None
    
    try:
        cached_value = redis_client.get(key)
        if cached_value is not None:
            try:
                # Try to deserialize JSON
                return json.loads(cached_value)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return as string
                return cached_value
        return None
    except RedisError as e:
        logger.warning(f"Redis get error for key {key}: {e}")
        return None


def set_cache(key: str, value: Any, ttl: int):
    """
    Set value in cache
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds
    """
    redis_client = get_redis_client()
    
    if not redis_client:
        return
    
    try:
        # Serialize value to JSON if it's not a string
        if isinstance(value, str):
            serialized_value = value
        else:
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                # If can't serialize, convert to string
                serialized_value = str(value)
        
        redis_client.setex(key, ttl, serialized_value)
        logger.debug(f"Cached key: {key} (TTL: {ttl}s)")
    except RedisError as e:
        logger.warning(f"Redis set error for key {key}: {e}")


def delete_cache(key: str):
    """
    Delete key from cache
    
    Args:
        key: Cache key to delete
    """
    redis_client = get_redis_client()
    
    if not redis_client:
        return
    
    try:
        redis_client.delete(key)
        logger.debug(f"Deleted cache key: {key}")
    except RedisError as e:
        logger.warning(f"Redis delete error for key {key}: {e}")


def delete_cache_pattern(pattern: str):
    """
    Delete all keys matching pattern
    
    Args:
        pattern: Redis key pattern (e.g., "chart:*")
    """
    redis_client = get_redis_client()
    
    if not redis_client:
        return
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Deleted {len(keys)} cache keys matching pattern: {pattern}")
    except RedisError as e:
        logger.warning(f"Redis delete pattern error for {pattern}: {e}")


def clear_all_cache():
    """Clear all cache keys"""
    redis_client = get_redis_client()
    
    if not redis_client:
        return
    
    try:
        redis_client.flushdb()
        logger.info("Cleared all Redis cache")
    except RedisError as e:
        logger.warning(f"Redis flushdb error: {e}")


def cache_exists(key: str) -> bool:
    """
    Check if key exists in cache
    
    Args:
        key: Cache key
        
    Returns:
        True if key exists, False otherwise
    """
    redis_client = get_redis_client()
    
    if not redis_client:
        return False
    
    try:
        return redis_client.exists(key) > 0
    except RedisError as e:
        logger.warning(f"Redis exists error for key {key}: {e}")
        return False

