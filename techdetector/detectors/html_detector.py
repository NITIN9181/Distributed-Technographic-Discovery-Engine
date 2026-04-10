"""
HTML source code detector.

Scans HTML content against technology signatures that define
``html`` detection vectors with regex or string match types.
"""

import logging
import re
from datetime import datetime, timezone

from techdetector.detectors.base import BaseDetector
from techdetector.models import Detection, DetectionVector, Technology

logger = logging.getLogger(__name__)


class HTMLDetector(BaseDetector):
    """Detects technologies by matching patterns against page HTML source."""

    def __init__(self, signatures: list[dict]) -> None:
        """Initialize with only signatures containing HTML detection vectors.

        Args:
            signatures: Full list of technology signature dicts.
        """
        html_sigs = [
            sig for sig in signatures
            if "html" in sig.get("detection_vectors", {})
        ]
        super().__init__(html_sigs)
        logger.debug("HTMLDetector loaded %d signatures", len(self.signatures))

    def detect(self, html: str) -> list[Detection]:
        """Scan HTML source for technology fingerprints.

        Args:
            html: Raw HTML string of the page.

        Returns:
            List of Detection objects for each matched technology.
        """
        if not html:
            return []

        detections: list[Detection] = []

        for sig in self.signatures:
            vectors = sig["detection_vectors"]["html"]
            patterns: list[str] = vectors.get("patterns", [])
            match_type: str = vectors.get("match_type", "regex")

            for pattern in patterns:
                matched = self._match(html, pattern, match_type)
                if matched:
                    tech = Technology(
                        id=sig["id"],
                        name=sig["name"],
                        category=sig["category"],
                    )
                    detections.append(
                        Detection(
                            technology=tech,
                            vector=DetectionVector.HTML_SOURCE,
                            evidence=f"Pattern matched: {pattern} -> {matched}",
                            detected_at=datetime.now(timezone.utc),
                        )
                    )
                    logger.info("HTML: Detected %s via pattern '%s'", sig["name"], pattern)
                    # One match per technology is enough — stop checking more patterns
                    break

        return detections

    @staticmethod
    def _match(html: str, pattern: str, match_type: str) -> str | None:
        """Attempt to match a pattern against HTML content.

        Args:
            html: The HTML string to search.
            pattern: The pattern (regex or literal string).
            match_type: Either ``"regex"`` or ``"string"``.

        Returns:
            The matched text if found, else None.
        """
        if match_type == "regex":
            try:
                m = re.search(pattern, html, re.IGNORECASE)
                return m.group(0) if m else None
            except re.error as exc:
                logger.warning("Invalid regex '%s': %s", pattern, exc)
                return None
        else:
            # Case-insensitive string search
            if pattern.lower() in html.lower():
                return pattern
            return None
