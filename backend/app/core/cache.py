"""Thin Redis cache wrapper used for market-data and indicator caching.

Falls back to a no-op in-memory dict if Redis is unreachable (e.g. running
unit tests without a Redis instance) so the rest of the app never has to
special-case "cache unavailable".
"""

import json
from typing import Any

import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class _InMemoryFallback:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value

    def delete(self, *keys: str) -> None:
        for key in keys:
            self._store.pop(key, None)

    def ping(self) -> bool:
        return True

    def scan_iter(self, match: str):
        prefix = match.rstrip("*")
        return [k for k in list(self._store) if k.startswith(prefix)]


class CacheClient:
    def __init__(self) -> None:
        try:
            self._client: Any = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            self._client.ping()
        except redis.RedisError:
            logger.warning("redis_unavailable_using_in_memory_fallback")
            self._client = _InMemoryFallback()

    def get_json(self, key: str) -> Any | None:
        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or settings.MARKET_DATA_CACHE_TTL_SECONDS
        self._client.setex(key, ttl, json.dumps(value, default=str))

    def invalidate(self, *keys: str) -> None:
        self._client.delete(*keys)

    def invalidate_prefix(self, prefix: str) -> None:
        """Drop every key starting with `prefix` (e.g. all cached date ranges of one symbol)."""
        keys = list(self._client.scan_iter(match=f"{prefix}*"))
        if keys:
            self._client.delete(*keys)


_cache_instance: CacheClient | None = None


def get_cache() -> CacheClient:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheClient()
    return _cache_instance
