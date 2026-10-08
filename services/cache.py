"""CLIMORA Safe In-Memory Query Caching Layer.

Provides deterministic, thread-safe, SHA-aware in-memory caching for immutable
canonical query results without introducing external network dependencies.
Guarantees cache never acts as a scientific source of truth and never masks mutable state.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any, Dict, Optional, Tuple


class QueryCacheManager:
    """Thread-safe, SHA-aware in-memory query cache with TTL and telemetry."""

    def __init__(self, max_entries: int = 500, default_ttl_sec: float = 300.0):
        self.max_entries = max_entries
        self.default_ttl_sec = default_ttl_sec
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    @staticmethod
    def generate_cache_key(
        prefix: str,
        artifact_sha: str,
        project_id: str,
        params: Optional[Dict[str, Any]] = None,
        schema_version: str = "v1",
    ) -> str:
        """Constructs a deterministic cache key binding artifact SHA, project, and query params."""
        normalized_params = ""
        if params:
            # Sort keys to ensure deterministic representation
            serialized = json.dumps(params, sort_keys=True, default=str)
            param_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
            normalized_params = f":{param_hash}"

        return f"climora:{schema_version}:{prefix}:{artifact_sha[:12]}:{project_id}{normalized_params}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieves a cached value if present and unexpired."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expire_at = self._cache[key]
            if time.time() > expire_at:
                # Expired
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl_sec: Optional[float] = None) -> None:
        """Caches a value with expiration and LRU eviction if full."""
        ttl = ttl_sec if ttl_sec is not None else self.default_ttl_sec
        expire_at = time.time() + ttl

        with self._lock:
            # Evict if exceeding max entries
            if len(self._cache) >= self.max_entries and key not in self._cache:
                # Remove oldest entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            self._cache[key] = (value, expire_at)

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidates all cache keys matching a given prefix."""
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if prefix in k]
            for k in keys_to_remove:
                del self._cache[k]
            return len(keys_to_remove)

    def clear(self) -> None:
        """Flushes the entire cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns cache telemetry statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = round((self._hits / total), 4) if total > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total,
                "hit_ratio": hit_ratio,
                "cached_entries_count": len(self._cache),
                "max_entries": self.max_entries,
            }

    @property
    def stats(self) -> Dict[str, Any]:
        """Property alias for get_telemetry()."""
        return self.get_telemetry()
