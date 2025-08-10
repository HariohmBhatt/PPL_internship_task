"""Redis caching service for improved performance."""

import json
import pickle
from typing import Any, Optional, Union

import redis.asyncio as redis
import structlog
from pydantic import BaseModel

from app.core.config import get_settings

logger = structlog.get_logger()


class CacheService:
    """Redis-based caching service."""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self._redis: Optional[redis.Redis] = None
        
    async def get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    self.settings.redis_url,
                    encoding="utf-8",
                    decode_responses=False  # We'll handle encoding ourselves
                )
                # Test connection
                await self._redis.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning("Redis connection failed, caching disabled", error=str(e))
                self._redis = None
                
        return self._redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.settings.cache_enabled:
            return None
            
        try:
            redis_client = await self.get_redis()
            if redis_client is None:
                return None
                
            value = await redis_client.get(key)
            if value is None:
                return None
                
            # Try JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except Exception as e:
            logger.warning("Cache get failed", key=key, error=str(e))
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        if not self.settings.cache_enabled:
            return False
            
        try:
            redis_client = await self.get_redis()
            if redis_client is None:
                return False
            
            # Use TTL from settings if not provided
            if ttl is None:
                ttl = self.settings.cache_ttl_seconds
            
            # Try JSON first, then pickle
            try:
                if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                    serialized_value = json.dumps(value, default=str).encode('utf-8')
                else:
                    serialized_value = pickle.dumps(value)
            except Exception:
                serialized_value = pickle.dumps(value)
            
            await redis_client.set(key, serialized_value, ex=ttl)
            return True
            
        except Exception as e:
            logger.warning("Cache set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.settings.cache_enabled:
            return False
            
        try:
            redis_client = await self.get_redis()
            if redis_client is None:
                return False
                
            await redis_client.delete(key)
            return True
            
        except Exception as e:
            logger.warning("Cache delete failed", key=key, error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.settings.cache_enabled:
            return 0
            
        try:
            redis_client = await self.get_redis()
            if redis_client is None:
                return 0
                
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                return len(keys)
            return 0
            
        except Exception as e:
            logger.warning("Cache clear pattern failed", pattern=pattern, error=str(e))
            return 0
    
    def get_quiz_cache_key(self, quiz_id: int) -> str:
        """Get cache key for quiz data."""
        return f"quiz:{quiz_id}"
    
    def get_quiz_questions_cache_key(self, quiz_id: int) -> str:
        """Get cache key for quiz questions."""
        return f"quiz_questions:{quiz_id}"
    
    def get_leaderboard_cache_key(self, subject: str, grade: str) -> str:
        """Get cache key for leaderboard."""
        return f"leaderboard:{subject}:{grade}"
    
    def get_user_stats_cache_key(self, user_id: int) -> str:
        """Get cache key for user statistics."""
        return f"user_stats:{user_id}"
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Global cache service instance
cache_service = CacheService()


class CacheManager:
    """Context manager for cache operations."""
    
    def __init__(self, cache: CacheService):
        self.cache = cache
    
    async def __aenter__(self) -> CacheService:
        return self.cache
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # Redis connection pooling handles cleanup automatically
        pass


def get_cache() -> CacheService:
    """Dependency to get cache service."""
    return cache_service
