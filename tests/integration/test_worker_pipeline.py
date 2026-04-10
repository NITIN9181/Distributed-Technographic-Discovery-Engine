"""
Integration tests for the worker processing pipeline.

Tests the DetectionProcessor with mocked crawl messages.
"""
import pytest
from datetime import datetime, timezone
from techdetector.workers.consumer import CrawlMessage
from techdetector.workers.processor import DetectionProcessor


def _make_crawl_message(domain: str = "test.example.com") -> CrawlMessage:
    """Create a test CrawlMessage with realistic data."""
    return CrawlMessage(
        message_id="test-msg-001",
        domain=domain,
        crawled_at=datetime.now(timezone.utc),
        html="""
        <html>
        <head>
            <script async src="https://www.googletagmanager.com/gtag/js?id=G-TEST"></script>
        </head>
        <body><p>Test page</p></body>
        </html>
        """,
        headers={
            "server": "cloudflare",
            "cf-ray": "test-SJC",
            "content-type": "text/html"
        },
        dns_records={},
        career_pages=[],
        tls_info={}
    )


class TestWorkerPipeline:
    """Tests for the detection processor pipeline."""

    @pytest.mark.asyncio
    async def test_process_message_returns_scan_result(self):
        """Verify process_message produces a valid ScanResult."""
        processor = DetectionProcessor.__new__(DetectionProcessor)

        from techdetector.scanner import _load_signatures
        from techdetector.detectors import HTMLDetector, HeaderDetector, DNSDetector, JobPostingDetector

        signatures = _load_signatures()
        processor.html_detector = HTMLDetector(signatures)
        processor.header_detector = HeaderDetector(signatures)
        processor.dns_detector = DNSDetector(signatures)
        processor.job_detector = JobPostingDetector(signatures)

        msg = _make_crawl_message()
        result = await processor.process_message(msg)

        assert result.domain == "test.example.com"
        assert result.html_fetched is True
        assert result.headers_captured is True
        assert isinstance(result.detections, list)

    @pytest.mark.asyncio
    async def test_process_message_with_empty_html(self):
        """Processor should handle empty HTML gracefully."""
        processor = DetectionProcessor.__new__(DetectionProcessor)

        from techdetector.scanner import _load_signatures
        from techdetector.detectors import HTMLDetector, HeaderDetector, DNSDetector, JobPostingDetector

        signatures = _load_signatures()
        processor.html_detector = HTMLDetector(signatures)
        processor.header_detector = HeaderDetector(signatures)
        processor.dns_detector = DNSDetector(signatures)
        processor.job_detector = JobPostingDetector(signatures)

        msg = _make_crawl_message()
        msg.html = ""
        msg.headers = {}

        result = await processor.process_message(msg)
        assert result.html_fetched is False
        assert result.headers_captured is False
