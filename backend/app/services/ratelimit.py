"""留言限频（FR-F87 / FR-F76）。

生产应使用 Redis（settings.REDIS_URL）。未配置时降级为进程内内存计数，
仅适用于单实例开发环境。
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from app.config import settings


class _MemBucket:
    def __init__(self) -> None:
        self.hits: deque[float] = deque()

    def allow(self, limit: int, window: float) -> bool:
        now = time.monotonic()
        while self.hits and now - self.hits[0] > window:
            self.hits.popleft()
        if len(self.hits) >= limit:
            return False
        self.hits.append(now)
        return True


_buckets: defaultdict[str, _MemBucket] = defaultdict(_MemBucket)


async def check_rate_limit(key: str) -> bool:
    limit = settings.CONTACT_LIMIT_PER_HOUR
    window = 3600.0
    return _buckets[key].allow(limit, window)
