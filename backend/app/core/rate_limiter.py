"""Redis-based rate limiter with sliding window algorithm."""
from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.database import get_redis


class RateLimiter:
    """Sliding window rate limiter using Redis."""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """Check if a request is allowed under the rate limit."""
        if self.redis is None:
            self.redis = await get_redis()

        current = await self.redis.get(key)

        if current is None:
            await self.redis.setex(key, window_seconds, "1")
            return True

        count = int(current)

        if count >= max_requests:
            return False

        await self.redis.incr(key)
        return True

    async def get_remaining(self, key: str, max_requests: int) -> int:
        """Get remaining requests in the current window."""
        if self.redis is None:
            self.redis = await get_redis()

        current = await self.redis.get(key)

        if current is None:
            return max_requests

        count = int(current)
        return max(0, max_requests - count)

    async def reset_limit(self, key: str) -> None:
        """Reset the rate limit for a key."""
        if self.redis is None:
            self.redis = await get_redis()

        await self.redis.delete(key)

    async def get_ttl(self, key: str) -> int:
        """Get remaining time in seconds for the current window."""
        if self.redis is None:
            self.redis = await get_redis()

        return await self.redis.ttl(key)


async def rate_limit(
    user_id: str,
    endpoint: str,
    max_per_minute: int = 60,
    max_per_hour: int = 1000
) -> tuple[bool, dict]:
    """Check rate limits for a user and endpoint."""
    redis = await get_redis()
    limiter = RateLimiter(redis)

    minute_key = f"ratelimit:minute:{user_id}:{endpoint}"
    hour_key = f"ratelimit:hour:{user_id}:{endpoint}"

    minute_allowed = await limiter.check_rate_limit(minute_key, max_per_minute, 60)
    if not minute_allowed:
        return False, {
            "error": "Rate limit exceeded",
            "retry_after": await limiter.get_ttl(minute_key)
        }

    hour_allowed = await limiter.check_rate_limit(hour_key, max_per_hour, 3600)
    if not hour_allowed:
        return False, {
            "error": "Hourly rate limit exceeded",
            "retry_after": await limiter.get_ttl(hour_key)
        }

    minute_remaining = await limiter.get_remaining(minute_key, max_per_minute)
    hour_remaining = await limiter.get_remaining(hour_key, max_per_hour)

    return True, {
        "remaining_minute": minute_remaining,
        "remaining_hour": hour_remaining
    }