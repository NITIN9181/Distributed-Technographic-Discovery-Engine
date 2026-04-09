"""
Google Analytics Detector

Fetches a webpage's HTML and pattern-matches against known Google Analytics
signatures to determine whether the site uses GA (Universal Analytics or GA4).

Usage:
    python detect.py <url>

Output:
    JSON to stdout with detection results.
"""

import json
import re
import sys
from typing import Optional

import requests


def fetch_html(url: str) -> Optional[str]:
    """Fetch the HTML content of a URL.

    Args:
        url: The fully-qualified URL to fetch.

    Returns:
        The response body as text, or None on any failure.
    """
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TechDetector/0.1)"},
        )
        response.raise_for_status()
        return response.text
    except Exception as exc:
        print(f"Error fetching {url}: {exc}", file=sys.stderr)
        return None


def detect_google_analytics(html: str) -> dict:
    """Detect Google Analytics signatures in HTML content.

    Searches for Universal Analytics (UA-*), GA4 (G-*), gtag.js,
    and analytics.js patterns.

    Args:
        html: Raw HTML string to scan.

    Returns:
        A dict with "detected" (bool) and "evidence" (list of matched patterns).
    """
    evidence: list[str] = []

    # Universal Analytics tracking IDs
    ua_matches = re.findall(r"UA-\d{4,10}-\d{1,4}", html)
    for match in ua_matches:
        if match not in evidence:
            evidence.append(match)

    # GA4 measurement IDs
    ga4_matches = re.findall(r"G-[A-Z0-9]{10,}", html)
    for match in ga4_matches:
        if match not in evidence:
            evidence.append(match)

    # gtag.js script reference
    if "googletagmanager.com/gtag/js" in html:
        evidence.append("gtag.js")

    # analytics.js script reference
    if "google-analytics.com/analytics.js" in html:
        evidence.append("analytics.js")

    return {"detected": len(evidence) > 0, "evidence": evidence}


def main() -> None:
    """Entry point: parse args, fetch HTML, detect GA, print JSON."""
    if len(sys.argv) < 2:
        print("Usage: python detect.py <url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    if not url.startswith(("http://", "https://")):
        print("Error: URL must start with http:// or https://", file=sys.stderr)
        sys.exit(1)

    html = fetch_html(url)

    if html is None:
        result = {
            "url": url,
            "google_analytics": {"detected": False, "evidence": []},
        }
    else:
        ga_result = detect_google_analytics(html)
        result = {"url": url, "google_analytics": ga_result}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
