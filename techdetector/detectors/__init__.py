"""
Detector modules for the technographic scanner.

Provides HTML source and HTTP header detection strategies
through a common BaseDetector interface.
"""

from .html_detector import HTMLDetector
from .header_detector import HeaderDetector
from .dns_detector import DNSDetector
from .job_posting_detector import JobPostingDetector

__all__ = ["HTMLDetector", "HeaderDetector", "DNSDetector", "JobPostingDetector"]
