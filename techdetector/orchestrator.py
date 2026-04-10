"""
Domain queue management.

Handles:
- Enqueueing domains for crawling
- Deduplication (don't re-queue recently crawled)
- Priority queuing
- Progress monitoring
"""

import redis
from datetime import datetime, timedelta
from typing import List


class Orchestrator:
    def __init__(self, redis_url: str, db_url: str):
        self.redis = redis.from_url(redis_url)
        self.db_url = db_url
        self.pending_queue = "domains:pending"
        self.crawled_set = "domains:crawled"

    def enqueue(
        self, domains: List[str], force: bool = False, skip_recent_hours: int = 24
    ):
        """
        Add domains to the crawl queue.

        Args:
            domains: List of domains to crawl
            force: If True, ignore recency check
            skip_recent_hours: Skip if crawled within this many hours
        """
        enqueued = 0
        skipped = 0

        for domain in domains:
            domain = self._normalize_domain(domain)

            if not force:
                # Check if recently crawled
                last_crawled = self.redis.zscore(self.crawled_set, domain)
                if last_crawled:
                    crawled_at = datetime.fromtimestamp(float(str(last_crawled))) # type: ignore
                    if datetime.now() - crawled_at < timedelta(hours=skip_recent_hours):
                        skipped += 1
                        continue

            # Add to pending queue
            self.redis.rpush(self.pending_queue, domain)
            enqueued += 1

        return {"enqueued": enqueued, "skipped": skipped}

    def mark_crawled(self, domain: str):
        """Mark a domain as crawled with timestamp."""
        self.redis.zadd(self.crawled_set, {domain: datetime.now().timestamp()})

    def get_queue_stats(self) -> dict:
        """Get current queue statistics."""
        pending = self.redis.llen(self.pending_queue)

        # Get stream info
        try:
            stream_info = self.redis.xinfo_stream("crawl:results")
            stream_length = stream_info.get("length", 0) if isinstance(stream_info, dict) else 0 # type: ignore
            consumer_groups = self.redis.xinfo_groups("crawl:results")
            pending_messages = sum(g.get("pending", 0) for g in consumer_groups) if isinstance(consumer_groups, list) else 0 # type: ignore
        except redis.ResponseError:
            stream_length = 0
            pending_messages = 0

        return {
            "domains_pending": pending,
            "messages_in_stream": stream_length,
            "messages_pending_ack": pending_messages,
            "total_crawled": self.redis.zcard(self.crawled_set),
        }

    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain: lowercase, strip www, strip protocol."""
        domain = domain.lower().strip()
        for prefix in ["https://", "http://", "www."]:
            if domain.startswith(prefix):
                domain = domain[len(prefix) :]
        return domain.rstrip("/")
