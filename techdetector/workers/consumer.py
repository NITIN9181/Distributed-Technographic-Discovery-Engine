"""
Redis Stream consumer for crawl results.

Uses consumer groups for distributed processing.
"""
import redis
import json
import os
import asyncio
from typing import Callable, AsyncIterator
from dataclasses import dataclass

@dataclass
class CrawlMessage:
    message_id: str
    domain: str
    html: str
    headers: dict
    dns_records: dict
    tls_info: dict
    career_pages: list[dict]
    crawled_at: str

class StreamConsumer:
    def __init__(
        self,
        redis_url: str,
        stream_name: str = "crawl:results",
        consumer_group: str = "detection_workers",
        consumer_name: str = None
    ):
        self.redis = redis.from_url(redis_url)
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"worker-{os.getpid()}"
        
    async def ensure_group(self):
        """Create consumer group if it doesn't exist."""
        try:
            self.redis.xgroup_create(
                self.stream_name, 
                self.consumer_group, 
                id='0', 
                mkstream=True
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    
    async def consume(self) -> AsyncIterator[CrawlMessage]:
        """
        Consume messages from stream.
        Uses XREADGROUP for distributed consumption.
        """
        while True:
            # XREADGROUP GROUP {group} {consumer} BLOCK 5000 STREAMS {stream} >
            messages = self.redis.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {self.stream_name: '>'},
                count=10,
                block=5000
            )
            
            for stream, stream_messages in messages or []:
                for message_id, data in stream_messages:
                    payload = json.loads(data[b'payload'])
                    payload.pop('message_id', None)
                    yield CrawlMessage(
                        message_id=message_id.decode(),
                        **payload
                    )
    
    async def ack(self, message_id: str):
        """Acknowledge message processing."""
        self.redis.xack(self.stream_name, self.consumer_group, message_id)
