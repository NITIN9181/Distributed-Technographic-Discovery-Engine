"""
CLI entry point for the technographic scanner.

Usage:
    python -m techdetector.scanner scan <url> [--vectors html,headers,dns,job_posting]
    python -m techdetector.scanner query --tech <technology_id>
    python -m techdetector.scanner query --vector <vector_name>
    python -m techdetector.scanner init-db
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from techdetector.models import ScanResult
from techdetector.storage import init_db, save_scan_result
from techdetector.fetcher import fetch_domain
from techdetector.career_crawler import discover_career_pages

from techdetector.detectors.html_detector import HTMLDetector
from techdetector.detectors.header_detector import HeaderDetector
from techdetector.detectors.dns_detector import DNSDetector
from techdetector.detectors.job_posting_detector import JobPostingDetector

logger = logging.getLogger(__name__)

_SIGNATURES_PATH = Path(__file__).parent / "signatures.json"


def _load_signatures() -> list[dict]:
    with open(_SIGNATURES_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("technologies", [])


def _normalize_domain(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    domain = domain.lower().strip(".")
    if domain.startswith("www."):
        domain = domain[4:]
    if ":" in domain:
        domain = domain.split(":")[0]
    return domain


def init_database():
    init_db()


def perform_scan(url: str, active_vectors: list[str]) -> ScanResult:
    domain = _normalize_domain(url)
    signatures = _load_signatures()
    all_detections = []

    html_fetched = False
    headers_captured = False

    if "html" in active_vectors or "headers" in active_vectors:
        fetch_result = fetch_domain(url)

        if fetch_result.error:
            logger.error(f"Fetch failed for {url}: {fetch_result.error}")
            print(f"\n  [ERROR] Fetching {url}: {fetch_result.error}\n")

        html_fetched = fetch_result.html is not None
        headers_captured = bool(fetch_result.headers)

        if "html" in active_vectors and fetch_result.html:
            html_detector = HTMLDetector(signatures)
            all_detections.extend(html_detector.detect(fetch_result.html))

        if "headers" in active_vectors and fetch_result.headers:
            header_detector = HeaderDetector(signatures)
            all_detections.extend(header_detector.detect(fetch_result.headers))

    if "dns" in active_vectors:
        dns_detector = DNSDetector(signatures)
        all_detections.extend(dns_detector.detect(domain))

    if "job_posting" in active_vectors:
        logger.info("Initializing NLP... gathering job postings...")
        job_detector = JobPostingDetector(signatures)
        career_res = discover_career_pages(domain)
        if career_res.aggregated_text:
            all_detections.extend(job_detector.detect(career_res.aggregated_text))

    # Deduplicate by technology ID
    seen = {}
    unique_detections = []
    for det in all_detections:
        tid = det.technology.id
        if tid not in seen:
            seen[tid] = True
            unique_detections.append(det)

    result = ScanResult(
        domain=domain,
        scan_timestamp=datetime.now(timezone.utc),
        detections=unique_detections,
        html_fetched=html_fetched,
        headers_captured=headers_captured,
    )

    save_scan_result(result)
    return result
