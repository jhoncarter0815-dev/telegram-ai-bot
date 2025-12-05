"""
Rate limiter implementation for API abuse prevention.
Uses in-memory storage with sliding window algorithm.
"""

import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Async-safe rate limiter with sliding window.
    Tracks requests per user within a time window.
    """
    
    def __init__(
        self,
        default_limit: int = 20,
        premium_limit: int = 1000,
        window_seconds: int = 3600  # 1 hour window
    ):
        self.default_limit = default_limit
        self.premium_limit = premium_limit
        self.window_seconds = window_seconds
        
        # Storage: {user_id: [(timestamp, count), ...]}
        self._requests: Dict[int, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def check_limit(
        self,
        user_id: int,
        is_premium: bool = False
    ) -> Tuple[bool, int, int]:
        """
        Check if user is within rate limit.
        
        Returns:
            Tuple of (is_allowed, current_count, limit)
        """
        async with self._lock:
            limit = self.premium_limit if is_premium else self.default_limit
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            # Clean old entries
            self._requests[user_id] = [
                (ts, count) for ts, count in self._requests[user_id]
                if ts > window_start
            ]
            
            # Count requests in window
            current_count = sum(count for _, count in self._requests[user_id])
            
            if current_count >= limit:
                return False, current_count, limit
            
            return True, current_count, limit
    
    async def record_request(self, user_id: int) -> None:
        """Record a new request for user."""
        async with self._lock:
            now = datetime.now()
            self._requests[user_id].append((now, 1))
    
    async def get_remaining(
        self,
        user_id: int,
        is_premium: bool = False
    ) -> int:
        """Get remaining requests for user."""
        is_allowed, current, limit = await self.check_limit(user_id, is_premium)
        return max(0, limit - current)
    
    async def get_reset_time(self, user_id: int) -> int:
        """Get seconds until rate limit resets."""
        async with self._lock:
            if not self._requests[user_id]:
                return 0
            
            oldest = min(ts for ts, _ in self._requests[user_id])
            reset_time = oldest + timedelta(seconds=self.window_seconds)
            remaining = (reset_time - datetime.now()).total_seconds()
            return max(0, int(remaining))
    
    async def clear_user(self, user_id: int) -> None:
        """Clear rate limit data for a user."""
        async with self._lock:
            self._requests.pop(user_id, None)
    
    async def cleanup_old_entries(self) -> None:
        """Periodic cleanup of old entries to prevent memory growth."""
        async with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            for user_id in list(self._requests.keys()):
                self._requests[user_id] = [
                    (ts, count) for ts, count in self._requests[user_id]
                    if ts > window_start
                ]
                if not self._requests[user_id]:
                    del self._requests[user_id]


# Global rate limiter instance
rate_limiter = RateLimiter()

