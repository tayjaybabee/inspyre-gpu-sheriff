"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: ratelimit.py

Description:
    Simple in-memory rate limiting + cooldown to prevent recovery loops.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from collections import deque


@dataclass
class RecoveryLimiter:
    cooldown_s: int
    max_attempts_per_10m: int
    _attempt_ts: deque[float] = field(default_factory=deque)
    _last_success_ts: float | None = None

    def can_attempt(self) -> tuple[bool, str]:
        now = time.time()

        # Cooldown after a successful recovery
        if self._last_success_ts is not None:
            since = now - self._last_success_ts
            if since < self.cooldown_s:
                return False, f'cooldown_active ({int(self.cooldown_s - since)}s remaining)'

        # Windowed attempt limit
        window_s = 600
        while self._attempt_ts and (now - self._attempt_ts[0]) > window_s:
            self._attempt_ts.popleft()

        if len(self._attempt_ts) >= self.max_attempts_per_10m:
            return False, f'rate_limited ({len(self._attempt_ts)}/{self.max_attempts_per_10m} in last 10m)'

        return True, 'ok'

    def note_attempt(self) -> None:
        self._attempt_ts.append(time.time())

    def note_success(self) -> None:
        self._last_success_ts = time.time()
