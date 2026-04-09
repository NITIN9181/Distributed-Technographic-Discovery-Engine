"""
CLI entry point for the technographic scanner.

Usage:
    python -m techdetector.scanner <url>
    python -m techdetector.scanner --query <domain>
    python -m techdetector.scanner --list-companies
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from techdetector.detectors import HeaderDetector, HtmlDetector
from techdetector.fetcher import fetch_domain
from techdetector.models import ScanResult
from techdetector.storage import get_all_companies, get_company_technologies, init_db, save_scan_result

logger = logging.getLogger(__name__)

_SIGNATURES_PATH = Path(__file__).parent / "signatures.json"
_DB_PATH = "./data/techdetector.db"


def _load_signatures() -> list[dict]:
    """Load technology signatures from the JSON file.

    Returns:
        List of technology signature dictionaries.
    """
    with open(_SIGNATURES_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    sigs = data.get("technologies", [])
    logger.info("Loaded %d technology signatures", len(sigs))
    return sigs


def _normalize_domain(url: str) -> str:
    """Extract and normalize a domain from a URL.

    Strips scheme, www., trailing slashes, and lowercases the result.

    Args:
        url: A URL or domain string.

    Returns:
        Normalized domain (e.g. ``"stripe.com"``).
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    domain = domain.lower().strip(".")

    # Strip www.
    if domain.startswith("www."):
        domain = domain[4:]

    # Strip port if present
    if ":" in domain:
        domain = domain.split(":")[0]

    return domain


def _print_scan_summary(result: ScanResult) -> None:
    """Print a human-readable scan summary to stdout.

    Args:
        result: The completed ScanResult.
    """
    print(f"\n{'='*60}")
    print(f"  Scan Results for: {result.domain}")
    print(f"  Scanned at: {result.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  HTML fetched: {'YES' if result.html_fetched else 'NO'}")
    print(f"  Headers captured: {'YES' if result.headers_captured else 'NO'}")
    print(f"{'='*60}")

    if not result.detections:
        print("\n  No technologies detected.\n")
        return

    print(f"\n  {len(result.detections)} technologies detected:\n")

    # Group by category
    by_category: dict[str, list] = {}
    for det in result.detections:
        cat = det.technology.category.upper()
        by_category.setdefault(cat, []).append(det)

    for category in sorted(by_category):
        print(f"  +-- {category}")
        for det in by_category[category]:
            vector_label = "HTML" if det.vector.value == "html_source" else "Header"
            print(f"  |   * {det.technology.name:<25} [{vector_label}]")
        print(f"  +{'='*44}")

    print()


def _print_query_results(domain: str, detections: list) -> None:
    """Print stored detection results for a domain.

    Args:
        domain: The queried domain.
        detections: List of Detection objects from the database.
    """
    print(f"\n{'='*60}")
    print(f"  Stored Technologies for: {domain}")
    print(f"{'='*60}")

    if not detections:
        print(f"\n  No records found for '{domain}'.")
        print("  Try scanning it first with: python -m techdetector.scanner <url>\n")
        return

    print(f"\n  {len(detections)} technologies on record:\n")

    by_category: dict[str, list] = {}
    for det in detections:
        cat = det.technology.category.upper()
        by_category.setdefault(cat, []).append(det)

    for category in sorted(by_category):
        print(f"  +-- {category}")
        for det in by_category[category]:
            vector_label = "HTML" if det.vector.value == "html_source" else "Header"
            print(f"  |   * {det.technology.name:<25} [{vector_label}]")
            print(f"  |     Evidence: {det.evidence[:70]}")
        print(f"  +{'='*44}")

    print()


def _print_companies(companies: list[dict]) -> None:
    """Print list of all scanned companies.

    Args:
        companies: List of company dicts from the database.
    """
    print(f"\n{'='*60}")
    print(f"  Scanned Companies ({len(companies)} total)")
    print(f"{'='*60}\n")

    if not companies:
        print("  No companies scanned yet.\n")
        return

    print(f"  {'Domain':<30} {'First Scanned':<22} {'Last Scanned':<22}")
    print(f"  {'-'*30} {'-'*22} {'-'*22}")

    for co in companies:
        print(f"  {co['domain']:<30} {co['first_scanned_at']:<22} {co['last_scanned_at']:<22}")

    print()


def scan(url: str) -> ScanResult:
    """Run a full technology scan on a URL.

    Fetches the page, runs HTML and header detectors, saves
    results to the database, and prints a summary.

    Args:
        url: The URL to scan.

    Returns:
        The completed ScanResult.
    """
    domain = _normalize_domain(url)
    signatures = _load_signatures()

    # Fetch
    fetch_result = fetch_domain(url)

    if fetch_result.error:
        logger.error("Fetch failed for %s: %s", url, fetch_result.error)
        print(f"\n  [ERROR] Fetching {url}: {fetch_result.error}\n")

    # Detect
    all_detections = []

    html_detector = HtmlDetector(signatures)
    header_detector = HeaderDetector(signatures)

    if fetch_result.html:
        html_detections = html_detector.detect(fetch_result.html)
        all_detections.extend(html_detections)

    if fetch_result.headers:
        header_detections = header_detector.detect(fetch_result.headers)
        all_detections.extend(header_detections)

    # Deduplicate by technology ID (prefer HTML over header if same tech)
    seen: dict[str, int] = {}
    unique_detections = []
    for det in all_detections:
        tid = det.technology.id
        if tid not in seen:
            seen[tid] = len(unique_detections)
            unique_detections.append(det)

    # Build result
    result = ScanResult(
        domain=domain,
        scan_timestamp=datetime.now(timezone.utc),
        detections=unique_detections,
        html_fetched=fetch_result.html is not None,
        headers_captured=bool(fetch_result.headers),
    )

    # Persist
    conn = init_db(_DB_PATH)
    try:
        save_scan_result(conn, result)
    finally:
        conn.close()

    # Print
    _print_scan_summary(result)

    return result


def query(domain: str) -> None:
    """Query and display stored technologies for a domain.

    Args:
        domain: The domain to look up.
    """
    normalized = _normalize_domain(domain)
    conn = init_db(_DB_PATH)
    try:
        detections = get_company_technologies(conn, normalized)
        _print_query_results(normalized, detections)
    finally:
        conn.close()


def list_companies() -> None:
    """List all companies in the database."""
    conn = init_db(_DB_PATH)
    try:
        companies = get_all_companies(conn)
        _print_companies(companies)
    finally:
        conn.close()


def main() -> None:
    """Parse arguments and dispatch to the appropriate command."""
    parser = argparse.ArgumentParser(
        prog="techdetector",
        description="Modular technographic scanner - detect 50+ technologies from any website.",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL to scan for technologies",
    )
    parser.add_argument(
        "--query", "-q",
        metavar="DOMAIN",
        help="Query stored results for a domain",
    )
    parser.add_argument(
        "--list-companies", "-l",
        action="store_true",
        help="List all previously scanned companies",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.list_companies:
        list_companies()
    elif args.query:
        query(args.query)
    elif args.url:
        scan(args.url)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
