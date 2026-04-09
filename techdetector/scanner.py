"""
CLI entry point for the technographic scanner.

Usage:
    python -m techdetector.scanner scan <url> [--vectors html,headers,dns,job_posting]
    python -m techdetector.scanner query --tech <technology_id>
    python -m techdetector.scanner query --vector <vector_name>
    python -m techdetector.scanner init-db
"""

import argparse
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from techdetector.config import load_config
from techdetector.models import ScanResult, DetectionVector
from techdetector.storage import init_db, save_scan_result, query_by_technology, query_by_vector, get_all_companies
from techdetector.fetcher import fetch_domain
from techdetector.career_crawler import discover_career_pages

from techdetector.detectors.html_detector import HtmlDetector
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
            html_detector = HtmlDetector(signatures)
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
    
    print_scan_summary(result)
    return result


def print_scan_summary(result: ScanResult):
    print(f"\n{'='*60}")
    print(f"  Scan Results for: {result.domain}")
    print(f"  Scanned at: {result.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}")
    
    if not result.detections:
        print("\n  No technologies detected.\n")
        return
        
    print(f"\n  {len(result.detections)} technologies detected:")
    for d in result.detections:
        print(f"   * {d.technology.name:<25} [{d.technology.category}] ({d.vector.value})")


def print_query_results(results: list[dict]):
    if not results:
        print("No results found.")
        return
        
    print(f"\nFound {len(results)} matches:\n")
    for r in results:
        v = r.get('last_verified_at', r.get('first_detected_at', ''))
        print(f"[{r['canonical_domain']}] {r['technology_id']} via {r['detection_vector']} (Last checked: {v})")


def main() -> None:
    parser = argparse.ArgumentParser(prog="techdetector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan Subcommand
    scan_parser = subparsers.add_parser("scan", help="Run a full or partial scan on a URL")
    scan_parser.add_argument("url", help="URL to scan")
    scan_parser.add_argument("--vectors", default="html,headers,dns,job_posting", help="Comma-separated vectors: html,headers,dns,job_posting")

    # query Subcommand
    query_parser = subparsers.add_parser("query", help="Query stored results")
    query_parser.add_argument("--tech", help="Query by technology ID (e.g., snowflake)")
    query_parser.add_argument("--vector", help="Query by vector (e.g., JOB_POSTING_NLP)")

    # init-db Subcommand
    init_parser = subparsers.add_parser("init-db", help="Initialize the database")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    # Make config load implicit
    load_config()

    if args.command == "init-db":
        init_database()
        print("Database initialized successfully.")
    elif args.command == "scan":
        vectors = [v.strip() for v in args.vectors.split(',')]
        perform_scan(args.url, vectors)
    elif args.command == "query":
        if args.tech:
            res = query_by_technology(args.tech)
            print_query_results(res)
        elif args.vector:
            # Map simple name to enum
            v_name = args.vector.upper()
            if v_name == "JOB_POSTING":
                v_name = "JOB_POSTING_NLP"
            try:
                vec = DetectionVector[v_name]
                res = query_by_vector(vec)
                print_query_results(res)
            except KeyError:
                print(f"Invalid vector {v_name}")
        else:
            print("Must specify --tech or --vector")
            query_parser.print_help()

if __name__ == "__main__":
    main()
