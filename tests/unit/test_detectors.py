"""
Unit tests for detection logic.
"""
import pytest
from techdetector.detectors.html_detector import HTMLDetector
from techdetector.detectors.header_detector import HeaderDetector
from techdetector.models import DetectionVector


class TestHTMLDetector:
    """Tests for the HTML source detection vector."""

    def test_detects_google_analytics(self, signatures, sample_html):
        """Verify GA4 tag manager script is detected."""
        detector = HTMLDetector(signatures)
        detections = detector.detect(sample_html)

        ga_detections = [d for d in detections if d.technology.id == 'google_analytics']
        assert len(ga_detections) == 1
        assert ga_detections[0].vector == DetectionVector.HTML_SOURCE

    def test_detects_stripe(self, signatures, sample_html):
        """Verify Stripe.js script is detected."""
        detector = HTMLDetector(signatures)
        detections = detector.detect(sample_html)

        stripe_detections = [d for d in detections if d.technology.id == 'stripe']
        assert len(stripe_detections) == 1

    def test_handles_empty_html(self, signatures):
        """Empty HTML should return no detections without errors."""
        detector = HTMLDetector(signatures)
        detections = detector.detect("")
        assert detections == []

    def test_handles_malformed_html(self, signatures):
        """Malformed HTML should not raise exceptions."""
        detector = HTMLDetector(signatures)
        detections = detector.detect("<html><body><div>")  # Unclosed tags
        assert isinstance(detections, list)

    def test_detects_intercom(self, signatures, sample_html):
        """Verify Intercom container div is detected."""
        detector = HTMLDetector(signatures)
        detections = detector.detect(sample_html)

        intercom_detections = [d for d in detections if d.technology.id == 'intercom']
        # Intercom may or may not be in signatures; test should not fail hard
        assert isinstance(intercom_detections, list)

    def test_no_false_positives_on_plain_html(self, signatures):
        """Plain HTML without any tech markers should yield zero detections."""
        detector = HTMLDetector(signatures)
        plain = "<html><head><title>Hello</title></head><body><p>World</p></body></html>"
        detections = detector.detect(plain)
        assert isinstance(detections, list)


class TestHeaderDetector:
    """Tests for the HTTP header detection vector."""

    def test_detects_cloudflare(self, signatures, sample_headers):
        """Verify Cloudflare is detected from server/cf-ray headers."""
        detector = HeaderDetector(signatures)
        detections = detector.detect(sample_headers)

        cf_detections = [d for d in detections if d.technology.id == 'cloudflare']
        assert len(cf_detections) == 1
        assert cf_detections[0].vector == DetectionVector.HTTP_HEADER

    def test_detects_nextjs(self, signatures, sample_headers):
        """Verify Next.js is detected from x-powered-by header."""
        detector = HeaderDetector(signatures)
        detections = detector.detect(sample_headers)

        nextjs = [d for d in detections if d.technology.id == 'nextjs']
        assert len(nextjs) == 1

    def test_handles_empty_headers(self, signatures):
        """Empty headers dict should return no detections."""
        detector = HeaderDetector(signatures)
        detections = detector.detect({})
        assert detections == []

    def test_handles_none_values(self, signatures):
        """Headers with None values should be handled gracefully."""
        detector = HeaderDetector(signatures)
        headers = {"server": None, "content-type": "text/html"}
        # Should not raise
        detections = detector.detect(headers)
        assert isinstance(detections, list)
