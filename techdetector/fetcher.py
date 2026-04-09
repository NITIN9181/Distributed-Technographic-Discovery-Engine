"""
HTTP fetching module for the technographic scanner.

Handles domain fetching with proper timeout, redirect following,
and header capture. Returns a FetchResult with both HTML body
and lowercase response headers.
"""

import logging
from typing import Optional

import requests
import aiohttp
from urllib.parse import urlparse

from techdetector.models import FetchResult
from techdetector.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT: int = 15
_MAX_REDIRECTS: int = 5
_USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def fetch_domain(url: str) -> FetchResult:
    """Fetch a URL and return both HTML body and response headers.

    Args:
        url: The URL to fetch.  If no scheme is provided, https:// is prepended.

    Returns:
        FetchResult containing the HTML body, response headers (lowercase keys),
        status code, and any error encountered.
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    logger.info("Fetching %s", url)

    session = requests.Session()
    session.max_redirects = _MAX_REDIRECTS
    session.headers.update({"User-Agent": _USER_AGENT})

    try:
        response = session.get(url, timeout=_DEFAULT_TIMEOUT, allow_redirects=True)
        html: Optional[str] = response.text if response.text else None
        headers: dict[str, str] = {
            k.lower(): v for k, v in response.headers.items()
        }
        final_url: str = response.url

        logger.info(
            "Fetched %s → %s  (status=%d, headers=%d, html_len=%d)",
            url,
            final_url,
            response.status_code,
            len(headers),
            len(html) if html else 0,
        )

        return FetchResult(
            url=url,
            final_url=final_url,
            html=html,
            headers=headers,
            status_code=response.status_code,
        )
    except requests.exceptions.TooManyRedirects:
        logger.error("Too many redirects for %s", url)
        return FetchResult(
            url=url,
            final_url=url,
            html=None,
            headers={},
            status_code=0,
            error="Too many redirects (limit: 5)",
        )
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching %s", url)
        return FetchResult(
            url=url,
            final_url=url,
            html=None,
            headers={},
            status_code=0,
            error="Connection timed out (15s)",
        )
    except requests.exceptions.RequestException as exc:
        logger.error("Error fetching %s: %s", url, exc)
        return FetchResult(
            url=url,
            final_url=url,
            html=None,
            headers={},
            status_code=0,
            error=str(exc),
        )

def extract_domain(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    return parsed.netloc

async def fetch_domain_async(
    session: aiohttp.ClientSession, 
    url: str,
    rate_limiter: RateLimiter
) -> FetchResult:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    domain = extract_domain(url)
    await rate_limiter.wait_for_slot(domain)

    logger.info("Async fetching %s", url)

    try:
        async with session.get(url, allow_redirects=True) as response:
            html = await response.text()
            headers = {k.lower(): v for k, v in response.headers.items()}
            final_url = str(response.url)

            logger.info(
                "Async fetched %s → %s  (status=%d, headers=%d, html_len=%d)",
                url,
                final_url,
                response.status,
                len(headers),
                len(html) if html else 0,
            )

            return FetchResult(
                url=url,
                final_url=final_url,
                html=html,
                headers=headers,
                status_code=response.status,
            )
    except Exception as exc:
        logger.error("Async error fetching %s: %s", url, exc)
        return FetchResult(
            url=url,
            final_url=url,
            html=None,
            headers={},
            status_code=0,
            error=str(exc),
        )
