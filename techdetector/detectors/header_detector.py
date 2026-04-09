"""
HTTP header detector.

Scans response headers against technology signatures that define
``headers`` detection vectors with exists / contains / equals / regex rules.
"""

import logging
import re
from datetime import datetime, timezone

from techdetector.detectors.base import BaseDetector
from techdetector.models import Detection, DetectionVector, Technology

logger = logging.getLogger(__name__)


class HeaderDetector(BaseDetector):
    """Detects technologies by inspecting HTTP response headers."""

    def __init__(self, signatures: list[dict]) -> None:
        """Initialize with only signatures containing header detection vectors.

        Args:
            signatures: Full list of technology signature dicts.
        """
        header_sigs = [
            sig for sig in signatures
            if "headers" in sig.get("detection_vectors", {})
        ]
        super().__init__(header_sigs)
        logger.debug("HeaderDetector loaded %d signatures", len(self.signatures))

    def detect(self, headers: dict[str, str]) -> list[Detection]:
        """Scan HTTP headers for technology fingerprints.

        Args:
            headers: Response headers with lowercase keys.

        Returns:
            List of Detection objects for each matched technology.
        """
        if not headers:
            return []

        detections: list[Detection] = []

        for sig in self.signatures:
            rules = sig["detection_vectors"]["headers"]
            if self._matches_rules(headers, rules):
                tech = Technology(
                    id=sig["id"],
                    name=sig["name"],
                    category=sig["category"],
                )
                evidence_parts = [
                    f"{hdr}={headers.get(hdr, '<missing>')}"
                    for hdr in rules
                ]
                detections.append(
                    Detection(
                        technology=tech,
                        vector=DetectionVector.HTTP_HEADER,
                        evidence=f"Header match: {'; '.join(evidence_parts)}",
                        detected_at=datetime.now(timezone.utc),
                    )
                )
                logger.info("Header: Detected %s", sig["name"])

        return detections

    @staticmethod
    def _matches_rules(headers: dict[str, str], rules: dict) -> bool:
        """Check whether headers satisfy ANY of the signature rules.

        A technology is detected if at least one header rule matches.

        Args:
            headers: Response headers (lowercase keys).
            rules: Dict mapping header names to matching conditions.

        Returns:
            True if at least one rule is satisfied.
        """
        for header_name, conditions in rules.items():
            header_name_lower = header_name.lower()
            header_value = headers.get(header_name_lower)

            if "exists" in conditions:
                if conditions["exists"] and header_value is not None:
                    return True
                if not conditions["exists"] and header_value is None:
                    return True

            if header_value is None:
                continue

            value_lower = header_value.lower()

            if "contains" in conditions:
                if conditions["contains"].lower() in value_lower:
                    return True

            if "equals" in conditions:
                if conditions["equals"].lower() == value_lower:
                    return True

            if "regex" in conditions:
                try:
                    if re.search(conditions["regex"], header_value, re.IGNORECASE):
                        return True
                except re.error as exc:
                    logger.warning(
                        "Invalid header regex '%s': %s", conditions["regex"], exc
                    )

        return False
