"""
DNS-based technology detection.

Analyzes MX, TXT, SPF, and CNAME records to detect:
- Email providers: Google Workspace, Microsoft 365, Zoho
- Email marketing: SendGrid, Mailchimp, Mailgun, Postmark
- Security: Proofpoint, Mimecast
- Verification: various SPF includes
"""

import logging
import dns.resolver
from techdetector.models import Detection, DetectionVector, Technology

logger = logging.getLogger(__name__)


class DNSDetector:
    def __init__(self, signatures: list[dict]):
        self.signatures = []
        for s in signatures:
            if "dns" in s.get("detection_vectors", {}):
                # Ensure the top-level keys are correct and convert vector formats
                tech = Technology(id=s["id"], name=s["name"], category=s["category"])
                self.signatures.append(
                    {"technology": tech, "dns_rules": s["detection_vectors"]["dns"]}
                )

    def detect_from_records(self, records: dict) -> list[Detection]:
        """Match against pre-fetched DNS records."""
        detections = []
        # Check against signatures
        for sig in self.signatures:
            detected = False
            evidence = ""

            rules = sig["dns_rules"]

            # Check MX matching
            if not detected and "mx" in rules:
                mx_contains = rules["mx"].get("contains", [])
                for target in mx_contains:
                    for exch in records.get("mx", []):
                        if target.lower() in exch:
                            detected = True
                            evidence = f"MX record matches {target}"
                            break
                    if detected:
                        break

            # Check TXT/SPF matching
            if not detected and "txt" in rules:
                txt_contains = rules["txt"].get("contains", [])
                for target in txt_contains:
                    for txt_rec in records.get("txt", []):
                        if target.lower() in txt_rec:
                            detected = True
                            evidence = f"TXT record matches: {target}"
                            break
                    if detected:
                        break

            if detected:
                detections.append(
                    Detection(
                        technology=sig["technology"],
                        vector=DetectionVector.DNS_RECORD,
                        evidence=evidence,
                    )
                )

        return detections

    def detect(self, domain: str) -> list[Detection]:
        """Query DNS records and match against signatures."""
        # Gather DNS records
        records: dict[str, list[str]] = {'mx': [], 'txt': [], 'cname': []}

        try:
            mx_answers = dns.resolver.resolve(domain, "MX")
            records["mx"] = [str(r.exchange).lower() for r in mx_answers]
        except Exception as e:
            logger.debug(f"MX lookup failed for {domain}: {e}")

        try:
            txt_answers = dns.resolver.resolve(domain, "TXT")
            records["txt"] = [str(r).lower().strip('"') for r in txt_answers]
        except Exception as e:
            logger.debug(f"TXT lookup failed for {domain}: {e}")

        return self.detect_from_records(records)
