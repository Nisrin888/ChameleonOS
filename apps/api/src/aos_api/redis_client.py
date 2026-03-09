"""
Redis client wrapper for Adaptive-OS.
Uses Upstash REST SDK for edge-compatible Redis.
Falls back to a mock in-memory implementation when no credentials are configured.
"""
import json
import time
from typing import Any

from aos_api.config import settings


class MockRedis:
    """In-memory Redis mock for local development without Upstash."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float | None]] = {}  # key -> (value, expire_at)

    def _is_expired(self, key: str) -> bool:
        if key not in self._store:
            return True
        _, expire_at = self._store[key]
        if expire_at and time.time() > expire_at:
            del self._store[key]
            return True
        return False

    async def get(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        value, _ = self._store[key]
        return value

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        expire_at = (time.time() + ex) if ex else None
        self._store[key] = (value, expire_at)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def incr(self, key: str) -> int:
        if self._is_expired(key):
            self._store[key] = ("0", None)
        val, expire_at = self._store[key]
        new_val = int(val) + 1
        self._store[key] = (str(new_val), expire_at)
        return new_val

    async def expire(self, key: str, seconds: int) -> None:
        if key in self._store:
            val, _ = self._store[key]
            self._store[key] = (val, time.time() + seconds)

    async def lpush(self, key: str, value: str) -> None:
        if self._is_expired(key):
            self._store[key] = ("[]", None)
        lst_str, expire_at = self._store[key]
        lst = json.loads(lst_str)
        lst.insert(0, value)
        self._store[key] = (json.dumps(lst), expire_at)

    async def rpop(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        lst_str, expire_at = self._store[key]
        lst = json.loads(lst_str)
        if not lst:
            return None
        item = lst.pop()
        self._store[key] = (json.dumps(lst), expire_at)
        return item


class UpstashRedisWrapper:
    """Wrapper around Upstash Redis REST client with the same async interface."""

    def __init__(self):
        from upstash_redis import Redis
        self._client = Redis(
            url=settings.upstash_redis_rest_url,
            token=settings.upstash_redis_rest_token,
        )

    async def get(self, key: str) -> str | None:
        result = self._client.get(key)
        return result

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        if ex:
            self._client.set(key, value, ex=ex)
        else:
            self._client.set(key, value)

    async def delete(self, key: str) -> None:
        self._client.delete(key)

    async def incr(self, key: str) -> int:
        return self._client.incr(key)

    async def expire(self, key: str, seconds: int) -> None:
        self._client.expire(key, seconds)

    async def lpush(self, key: str, value: str) -> None:
        self._client.lpush(key, value)

    async def rpop(self, key: str) -> str | None:
        return self._client.rpop(key)


# Singleton
_redis_client: MockRedis | UpstashRedisWrapper | None = None


async def init_redis() -> MockRedis | UpstashRedisWrapper:
    global _redis_client
    if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
        _redis_client = UpstashRedisWrapper()
        print("[AOS] Using Upstash Redis")
    else:
        _redis_client = MockRedis()
        print("[AOS] Using in-memory mock Redis (no Upstash credentials)")
    return _redis_client


async def close_redis():
    global _redis_client
    _redis_client = None


def get_redis() -> MockRedis | UpstashRedisWrapper:
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client
