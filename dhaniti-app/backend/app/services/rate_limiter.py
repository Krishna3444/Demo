"""
rate_limiter.py — simple in-memory sliding-window rate limiter.

Used to protect login, OTP, registration and password-reset endpoints from
brute-force / spam. Keys are arbitrary strings ("ip:1.2.3.4", "email:x@y.z").

Note: state is per-process (single uvicorn worker). For multi-worker
deployments swap the store for Redis — the interface stays identical.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_events: int, window_seconds: int):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        events = self._events[key]
        cutoff = now - self.window_seconds
        while events and events[0] < cutoff:
            events.popleft()
        return events

    def check(self, key: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        with self._lock:
            events = self._prune(key, now)
            if len(events) >= self.max_events:
                retry_after = int(self.window_seconds - (now - events[0])) + 1
                return False, max(retry_after, 1)
            events.append(now)
            return True, 0

    def reset(self, key: str) -> None:
        """Clear the window for a key (e.g. after a successful login)."""
        with self._lock:
            self._events.pop(key, None)
