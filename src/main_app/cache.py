"""Thread-safe TTL cache for reducing database queries."""
import threading
import time


class TTLCache:
    """Simple thread-safe cache with time-to-live expiration."""

    def __init__(self, ttl_seconds: int = 30):
        self._cache = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds

    def get(self, key: str):
        """Get cached value if not expired, else return None."""
        with self._lock:
            if key in self._cache:
                value, expires = self._cache[key]
                if time.time() < expires:
                    return value
                del self._cache[key]
        return None

    def set(self, key: str, value):
        """Set cached value with TTL."""
        with self._lock:
            self._cache[key] = (value, time.time() + self._ttl)

    def invalidate(self, key: str = None):
        """Invalidate specific key or entire cache."""
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()
