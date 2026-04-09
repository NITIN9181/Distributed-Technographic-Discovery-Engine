"""
Distributed-ready token bucket rate limiter.

For Phase 3, this is in-memory per-process.
In Phase 4, this will use Redis for distributed rate limiting.
"""
import asyncio
from dataclasses import dataclass, field
from time import monotonic
from typing import Dict

@dataclass
class TokenBucket:
    capacity: float          # Max tokens
    refill_rate: float       # Tokens per second
    tokens: float = field(default=0.0)
    last_refill: float = field(default_factory=monotonic)
    
    def __post_init__(self):
        # Start with full bucket
        if self.tokens == 0.0:
            self.tokens = self.capacity
            
    def _refill(self):
        now = monotonic()
        elapsed = now - self.last_refill
        
        if elapsed > 0:
            new_tokens = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
            
    def try_acquire(self) -> bool:
        """Non-blocking acquire. Returns True if token available."""
        self._refill()
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False
    
    async def acquire(self):
        """Blocking acquire. Waits until token is available."""
        while not self.try_acquire():
            # Calculate time to next token
            self._refill()
            tokens_needed = 1.0 - self.tokens
            wait_time = max(0.01, tokens_needed / self.refill_rate)
            await asyncio.sleep(wait_time)

class RateLimiter:
    def __init__(self, 
                 default_rate: float = 2.0,      # requests per second
                 default_burst: float = 5.0):    # max burst
        self.default_rate = default_rate
        self.default_burst = default_burst
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = asyncio.Lock()
    
    async def get_bucket(self, domain: str) -> TokenBucket:
        """Get or create bucket for domain."""
        async with self.lock:
            if domain not in self.buckets:
                self.buckets[domain] = TokenBucket(
                    capacity=self.default_burst,
                    refill_rate=self.default_rate
                )
            return self.buckets[domain]
    
    async def wait_for_slot(self, domain: str):
        """Wait until we can make a request to this domain."""
        bucket = await self.get_bucket(domain)
        await bucket.acquire()
    
    async def update_from_robots(self, domain: str, crawl_delay: float):
        """Adjust rate based on robots.txt crawl-delay."""
        bucket = await self.get_bucket(domain)
        # Crawl delay is seconds per request, so rate is 1.0 / delay
        rate = 1.0 / crawl_delay if crawl_delay > 0 else self.default_rate
        
        # We don't override if the user has requested a slower default rate.
        rate = min(rate, self.default_rate)
        
        bucket.refill_rate = rate
        # Burst capacity shouldn't bypass long crawl delays to be safe
        bucket.capacity = max(1.0, min(self.default_burst, rate * 2.0))
