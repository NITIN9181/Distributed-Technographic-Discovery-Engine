"""
Detection pipeline that processes crawl messages.
"""
import asyncio
import logging
from .consumer import StreamConsumer, CrawlMessage
from ..detectors import HTMLDetector, HeaderDetector, DNSDetector, JobPostingDetector
from ..storage import save_scan_result
from ..models import ScanResult, Detection

logger = logging.getLogger(__name__)

from ..scanner import _load_signatures

class DetectionProcessor:
    def __init__(self, redis_url: str, db_url: str):
        self.consumer = StreamConsumer(redis_url)
        signatures = _load_signatures()
        self.html_detector = HTMLDetector(signatures)
        self.header_detector = HeaderDetector(signatures)
        self.dns_detector = DNSDetector(signatures)
        self.job_detector = JobPostingDetector(signatures)
        self.db_url = db_url
    
    async def process_message(self, msg: CrawlMessage) -> ScanResult:
        """Run all 4 detection vectors on a crawl result."""
        detections = []
        
        # HTML detection
        if msg.html:
            detections.extend(self.html_detector.detect(msg.html))
        
        # Header detection
        if msg.headers:
            detections.extend(self.header_detector.detect(msg.headers))
        
        # DNS detection
        if msg.dns_records:
            detections.extend(self.dns_detector.detect_from_records(msg.dns_records))
        
        # Job posting NLP detection
        for career_page in msg.career_pages:
            if career_page.get('html'):
                detections.extend(self.job_detector.detect(career_page['html']))
        
        return ScanResult(
            domain=msg.domain,
            scan_timestamp=msg.crawled_at,  # Need to ensure this is parsed appropriately if needed
            detections=detections,
            html_fetched=bool(msg.html),
            headers_captured=bool(msg.headers),
            dns_resolved=bool(msg.dns_records),
            careers_crawled=len(msg.career_pages)
        )
    
    async def run(self):
        """Main worker loop."""
        await self.consumer.ensure_group()
        
        async for message in self.consumer.consume():
            try:
                import datetime
                if isinstance(message.crawled_at, str):
                    try:
                        message.crawled_at = datetime.datetime.fromisoformat(message.crawled_at.replace("Z", "+00:00"))
                    except Exception:
                        message.crawled_at = datetime.datetime.now(datetime.timezone.utc)
                
                result = await self.process_message(message)
                # save_scan_result handles persistence logic
                save_scan_result(result)
                await self.consumer.ack(message.message_id)
                logger.info(f"Processed {message.domain}: {len(result.detections)} technologies")
            except Exception as e:
                logger.error(f"Failed to process {message.domain}: {e}")
                import traceback
                traceback.print_exc()
                # Don't ack - message will be redelivered
