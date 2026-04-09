"""
Detector modules for the technographic scanner.

Provides HTML source and HTTP header detection strategies
through a common BaseDetector interface.
"""

from techdetector.detectors.html_detector import HtmlDetector
from techdetector.detectors.header_detector import HeaderDetector

__all__ = ["HtmlDetector", "HeaderDetector"]
