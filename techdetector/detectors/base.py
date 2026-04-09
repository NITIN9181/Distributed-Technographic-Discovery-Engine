"""
Abstract base class for technology detectors.

All detection strategies (HTML, headers, DNS, etc.) must implement
this interface so the scanner can orchestrate them uniformly.
"""

from abc import ABC, abstractmethod
from typing import Any

from techdetector.models import Detection


class BaseDetector(ABC):
    """Abstract detector that all concrete detectors must subclass."""

    def __init__(self, signatures: list[dict]) -> None:
        """Initialize with a list of technology signature dicts.

        Args:
            signatures: Technology definitions loaded from signatures.json.
        """
        self.signatures = signatures

    @abstractmethod
    def detect(self, data: Any) -> list[Detection]:
        """Run detection against the provided data.

        Args:
            data: Input data to scan (HTML string, header dict, etc.).

        Returns:
            List of Detection objects for every matched technology.
        """
        ...
