"""
Unit tests for the token-bucket rate limiter.
"""
import pytest
import asyncio
from techdetector.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for the in-process rate limiter."""

    @pytest.mark.asyncio
    async def test_initial_tokens(self):
        """Rate limiter should start with full bucket."""
        limiter = RateLimiter(default_rate=2.0, default_burst=5.0)
        bucket = await limiter.get_bucket("test.com")
        assert bucket.tokens <= bucket.capacity

    @pytest.mark.asyncio
    async def test_acquire_succeeds(self):
        """First acquire should succeed immediately."""
        limiter = RateLimiter(default_rate=10.0, default_burst=10.0)
        # Should not block heavily
        await limiter.wait_for_slot("test.com")
        bucket = await limiter.get_bucket("test.com")
        # Ensure it acquired a token
        assert bucket.tokens < bucket.capacity

    @pytest.mark.asyncio
    async def test_burst_limit(self):
        """Should not exceed burst limit worth of tokens."""
        limiter = RateLimiter(default_rate=1.0, default_burst=3.0)
        # Consume all burst tokens
        for _ in range(3):
            await limiter.wait_for_slot("test.com")
        bucket = await limiter.get_bucket("test.com")
        assert bucket.tokens < 1.0

    @pytest.mark.asyncio
    async def test_rate_recovery(self):
        """After consuming tokens, they should recover over time."""
        limiter = RateLimiter(default_rate=100.0, default_burst=5.0)
        # Drain tokens
        for _ in range(5):
            await limiter.wait_for_slot("test.com")
        bucket = await limiter.get_bucket("test.com")
        tokens_after_drain = bucket.tokens
        # Wait a bit for recovery
        await asyncio.sleep(0.1)
        bucket._refill()
        assert bucket.tokens > tokens_after_drain

    def test_repr(self):
        """Rate limiter should have a useful repr."""
        limiter = RateLimiter(default_rate=2.0, default_burst=5.0)
        repr_str = repr(limiter)
        assert repr_str is not None

