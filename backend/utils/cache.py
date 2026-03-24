"""
TTL-based in-memory cache for tool results.
Reduces redundant LLM and API calls.
"""

from __future__ import annotations

import time
from threading import Lock
from typing import Any, Optional


class TTLCache:
    """Thread-safe TTL in-memory cache."""

    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            expires_at = time.monotonic() + (ttl or self._default_ttl)
            self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def evict_expired(self) -> int:
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
        return len(expired)


# Singleton cache instance used across tools
cache = TTLCache(default_ttl=300)
