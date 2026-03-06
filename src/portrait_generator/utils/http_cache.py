"""Persistent HTTP response cache for Wikipedia / Wikidata / Wikimedia API calls.

Prevents repeated requests to the same public APIs across portrait-generation runs,
avoiding rate-limiting and 403 blocks from Wikimedia, Wikipedia, and DBpedia.

Usage (module-level singleton — just import and use):
    from .http_cache import HTTP_CACHE

    data = HTTP_CACHE.get_json(url, params)
    if data is None:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            HTTP_CACHE.put_json(url, params, data)

Cache layout:
    ~/.cache/portrait_generator/http_responses/{32-char-md5}.json
    Each file: {"timestamp": <unix float>, "url": "...", "data": <json>}

Default TTL: 30 days.  Biographical data from Wikidata / Wikipedia is stable.
The cache is shared across all portrait-generation runs on the same machine.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


# Global cache location; override by passing cache_dir to HttpResponseCache()
_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "portrait_generator" / "http_responses"
_DEFAULT_TTL_DAYS = 30


class HttpResponseCache:
    """Persistent on-disk JSON cache for HTTP API responses.

    Thread-safe for concurrent portrait generations: uses atomic file rename
    so partial writes are never visible to other processes.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_days: int = _DEFAULT_TTL_DAYS,
    ) -> None:
        self._cache_dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
        self._ttl_seconds = ttl_days * 86_400
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass  # Read-only filesystem or permission issue — cache will be no-op

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """Return cached JSON data if present and not expired; else None.

        Args:
            url: The full request URL (without query string).
            params: Query-parameter dict passed to requests.get().

        Returns:
            Cached deserialized JSON (dict/list/etc.) or None on miss.
        """
        path = self._cache_path(self._cache_key(url, params))
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            age = time.time() - float(raw.get("timestamp", 0))
            if age > self._ttl_seconds:
                path.unlink(missing_ok=True)
                return None
            return raw["data"]
        except Exception:
            return None

    def put_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]],
        data: Any,
    ) -> None:
        """Persist JSON-serializable data to the cache.

        Silently skips on any error (disk full, read-only FS, etc.) so the
        caller never needs to handle cache failures.

        Args:
            url: The full request URL.
            params: Query-parameter dict.
            data: JSON-serializable response data (dict, list, etc.).
        """
        key = self._cache_key(url, params)
        path = self._cache_path(key)
        try:
            payload = json.dumps(
                {"timestamp": time.time(), "url": url, "data": data},
                ensure_ascii=False,
                indent=2,
            )
            # Atomic write: write to .tmp then rename, so partial writes are invisible
            tmp = path.with_suffix(".tmp")
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(path)
        except Exception:
            pass  # Never crash on cache write failures

    def invalidate(self, url: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Remove a specific cached entry (e.g., after a known data update)."""
        path = self._cache_path(self._cache_key(url, params))
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass

    def clear_expired(self) -> int:
        """Remove all expired cache entries. Returns count removed."""
        removed = 0
        try:
            for path in self._cache_dir.glob("*.json"):
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    age = time.time() - float(raw.get("timestamp", 0))
                    if age > self._ttl_seconds:
                        path.unlink(missing_ok=True)
                        removed += 1
                except Exception:
                    continue
        except Exception:
            pass
        return removed

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _cache_key(self, url: str, params: Optional[Dict[str, Any]]) -> str:
        """Stable MD5 key from URL + sorted params."""
        key_str = url
        if params:
            key_str += "?" + "&".join(
                f"{k}={v}" for k, v in sorted(params.items(), key=lambda kv: str(kv[0]))
            )
        return hashlib.md5(key_str.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.json"


# ---------------------------------------------------------------------------
# Module-level singleton — imported and shared by ground_truth.py and
# reference_finder.py so both modules benefit from the same cache.
# ---------------------------------------------------------------------------
HTTP_CACHE = HttpResponseCache()
