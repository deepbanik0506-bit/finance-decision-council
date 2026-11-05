"""In-process request throttling.

Suitable for a single Render instance. It protects Groq quota from casual
abuse; it is not a distributed rate limiter.
"""

import threading
import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> float | None:
        """Record a hit. Returns None if allowed, else seconds until retry."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(0.0, self.window - (now - hits[0]))
            hits.append(now)
            if len(self._hits) > 10_000:
                self._prune(now)
            return None

    def _prune(self, now: float) -> None:
        stale = [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window]
        for key in stale:
            del self._hits[key]


class ConcurrencyGate:
    """Caps simultaneous council executions without queueing."""

    def __init__(self, limit: int):
        self._semaphore = threading.BoundedSemaphore(limit)

    def try_acquire(self) -> bool:
        return self._semaphore.acquire(blocking=False)

    def release(self) -> None:
        self._semaphore.release()
