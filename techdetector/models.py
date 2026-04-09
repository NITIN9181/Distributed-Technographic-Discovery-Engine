"""
Data models for the technographic scanner.

Defines the core data classes used throughout the detection pipeline:
Technology, Detection, ScanResult, and FetchResult.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DetectionVector(Enum):
    """Enumeration of supported detection methods."""

    HTML_SOURCE = "html_source"
    HTTP_HEADER = "http_header"
    DNS_RECORD = "dns_record"      # Placeholder for Phase 2
    JOB_POSTING = "job_posting"    # Placeholder for Phase 2


@dataclass
class Technology:
    """Represents a detectable technology."""

    id: str
    name: str
    category: str


@dataclass
class Detection:
    """A single technology detection event."""

    technology: Technology
    vector: DetectionVector
    evidence: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FetchResult:
    """Result of fetching a URL."""

    url: str
    final_url: str
    html: Optional[str]
    headers: dict[str, str]
    status_code: int
    error: Optional[str] = None


@dataclass
class ScanResult:
    """Aggregated result of a full domain scan."""

    domain: str
    scan_timestamp: datetime
    detections: list[Detection]
    html_fetched: bool
    headers_captured: bool
