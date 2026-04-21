import threading
import time
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self._ttl = max(0, int(ttl_seconds))
        self._lock = threading.Lock()
        self._data = {}  # type: Dict[str, Tuple[float, Any]]

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            expires_at, value = item
            if expires_at < now:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        if self._ttl <= 0:
            return
        expires_at = time.time() + self._ttl
        with self._lock:
            self._data[key] = (expires_at, value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

