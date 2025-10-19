"""
Redis Caching Layer for Adaptive Learning Platform

Caches frequently accessed data to reduce database load and improve response times:
- Learner profiles
- Learning journeys
- Topic mastery scores
- Performance analysis results
- Recommendations

Uses Redis with TTL (Time To Live) for automatic cache invalidation.
"""

import redis
import json
import os
from typing import Optional, Dict, List, Any
from functools import wraps
import hashlib

# Redis client initialization
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,  # Auto-decode bytes to strings
    socket_connect_timeout=5,
    socket_timeout=5
)


def is_redis_available() -> bool:
    """Check if Redis is available and responsive"""
    try:
        redis_client.ping()
        return True
    except (redis.ConnectionError, redis.TimeoutError):
        return False


class CacheKeys:
    """Centralized cache key management"""

    @staticmethod
    def learner_profile(user_id: str) -> str:
        return f"learner_profile:{user_id}"

    @staticmethod
    def learning_journey(user_id: str) -> str:
        return f"learning_journey:{user_id}"

    @staticmethod
    def topic_mastery(user_id: str, topic: str) -> str:
        return f"topic_mastery:{user_id}:{topic}"

    @staticmethod
    def all_topic_mastery(user_id: str) -> str:
        return f"all_topic_mastery:{user_id}"

    @staticmethod
    def performance_analysis(user_id: str) -> str:
        return f"performance_analysis:{user_id}"

    @staticmethod
    def recommendations(user_id: str) -> str:
        return f"recommendations:{user_id}"

    @staticmethod
    def agent_activity(user_id: str) -> str:
        return f"agent_activity:{user_id}"

    @staticmethod
    def quiz_history(user_id: str, limit: int = 20) -> str:
        return f"quiz_history:{user_id}:limit_{limit}"


class CacheTTL:
    """Time To Live values in seconds"""
    LEARNER_PROFILE = 3600  # 1 hour
    LEARNING_JOURNEY = 1800  # 30 minutes
    TOPIC_MASTERY = 1800  # 30 minutes
    PERFORMANCE_ANALYSIS = 600  # 10 minutes
    RECOMMENDATIONS = 300  # 5 minutes
    AGENT_ACTIVITY = 600  # 10 minutes
    QUIZ_HISTORY = 300  # 5 minutes


def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found/error
    """
    if not is_redis_available():
        return None

    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except (redis.RedisError, json.JSONDecodeError) as e:
        print(f"Cache get error for key {key}: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int) -> bool:
    """
    Set value in cache with TTL

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds

    Returns:
        True if successful, False otherwise
    """
    if not is_redis_available():
        return False

    try:
        serialized = json.dumps(value)
        redis_client.setex(key, ttl, serialized)
        return True
    except (redis.RedisError, TypeError, json.JSONEncodeError) as e:
        print(f"Cache set error for key {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """
    Delete value from cache

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    if not is_redis_available():
        return False

    try:
        redis_client.delete(key)
        return True
    except redis.RedisError as e:
        print(f"Cache delete error for key {key}: {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern

    Args:
        pattern: Redis pattern (e.g., "user:123:*")

    Returns:
        Number of keys deleted
    """
    if not is_redis_available():
        return 0

    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except redis.RedisError as e:
        print(f"Cache delete pattern error for {pattern}: {e}")
        return 0


def invalidate_user_cache(user_id: str):
    """
    Invalidate all cache entries for a user

    Called when user data changes significantly (e.g., after quiz, onboarding update)
    """
    patterns = [
        f"*:{user_id}",
        f"*:{user_id}:*"
    ]

    deleted = 0
    for pattern in patterns:
        deleted += cache_delete_pattern(pattern)

    print(f"Invalidated {deleted} cache entries for user {user_id}")


# --- Convenience Functions for Specific Data ---

def get_cached_learner_profile(user_id: str) -> Optional[Dict]:
    """Get cached learner profile"""
    return cache_get(CacheKeys.learner_profile(user_id))


def set_cached_learner_profile(user_id: str, profile: Dict) -> bool:
    """Cache learner profile"""
    return cache_set(
        CacheKeys.learner_profile(user_id),
        profile,
        CacheTTL.LEARNER_PROFILE
    )


def get_cached_learning_journey(user_id: str) -> Optional[List[Dict]]:
    """Get cached learning journey"""
    return cache_get(CacheKeys.learning_journey(user_id))


def set_cached_learning_journey(user_id: str, journey: List[Dict]) -> bool:
    """Cache learning journey"""
    return cache_set(
        CacheKeys.learning_journey(user_id),
        journey,
        CacheTTL.LEARNING_JOURNEY
    )


def get_cached_performance_analysis(user_id: str) -> Optional[Dict]:
    """Get cached performance analysis"""
    return cache_get(CacheKeys.performance_analysis(user_id))


def set_cached_performance_analysis(user_id: str, analysis: Dict) -> bool:
    """Cache performance analysis"""
    return cache_set(
        CacheKeys.performance_analysis(user_id),
        analysis,
        CacheTTL.PERFORMANCE_ANALYSIS
    )


def get_cached_recommendations(user_id: str) -> Optional[Dict]:
    """Get cached recommendations"""
    return cache_get(CacheKeys.recommendations(user_id))


def set_cached_recommendations(user_id: str, recommendations: Dict) -> bool:
    """Cache recommendations"""
    return cache_set(
        CacheKeys.recommendations(user_id),
        recommendations,
        CacheTTL.RECOMMENDATIONS
    )


def get_cached_topic_mastery(user_id: str) -> Optional[List[Dict]]:
    """Get cached all topic mastery"""
    return cache_get(CacheKeys.all_topic_mastery(user_id))


def set_cached_topic_mastery(user_id: str, mastery: List[Dict]) -> bool:
    """Cache all topic mastery"""
    return cache_set(
        CacheKeys.all_topic_mastery(user_id),
        mastery,
        CacheTTL.TOPIC_MASTERY
    )


# --- Quiz Caching ---

def cache_quiz(quiz_id: str, quiz_data: Dict) -> bool:
    """
    Cache quiz data for submission validation
    TTL: 1 hour (quiz should be completed within this time)
    """
    return cache_set(f"quiz:{quiz_id}", quiz_data, ttl=3600)


def get_cached_quiz(quiz_id: str) -> Optional[Dict]:
    """Get cached quiz data"""
    return cache_get(f"quiz:{quiz_id}")


def clear_cached_quiz(quiz_id: str) -> bool:
    """Clear cached quiz after submission"""
    return cache_delete(f"quiz:{quiz_id}")


# --- Decorator for automatic caching ---

def cached(key_func, ttl: int):
    """
    Decorator for automatic function caching

    Args:
        key_func: Function that generates cache key from function args
        ttl: Time to live in seconds

    Example:
        @cached(lambda user_id: f"profile:{user_id}", 3600)
        def get_user_profile(user_id):
            # expensive operation
            return profile
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_func(*args, **kwargs)

            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                print(f"Cache HIT: {cache_key}")
                return cached_value

            # Cache miss - call function
            print(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            if result is not None:
                cache_set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# --- Health Check ---

def cache_health_check() -> Dict[str, Any]:
    """
    Check Redis cache health

    Returns:
        Dictionary with health status and metrics
    """
    try:
        # Ping test
        redis_client.ping()

        # Get info
        info = redis_client.info()

        return {
            "status": "healthy",
            "connected": True,
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace": redis_client.dbsize()
        }
    except (redis.ConnectionError, redis.TimeoutError) as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test Redis connection
    print("Testing Redis connection...")
    print(f"Redis available: {is_redis_available()}")

    if is_redis_available():
        print("\nRedis Health Check:")
        health = cache_health_check()
        print(json.dumps(health, indent=2))

        # Test cache operations
        print("\nTesting cache operations...")
        test_key = "test:cache"
        test_value = {"message": "Hello Redis", "number": 42}

        print(f"Setting: {test_key} = {test_value}")
        cache_set(test_key, test_value, 60)

        print(f"Getting: {test_key}")
        retrieved = cache_get(test_key)
        print(f"Retrieved: {retrieved}")

        print(f"Deleting: {test_key}")
        cache_delete(test_key)

        print("✓ Cache operations successful!")
    else:
        print("✗ Redis is not available")
