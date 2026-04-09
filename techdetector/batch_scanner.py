"""
Async batch scanner for processing multiple domains.

Uses asyncio.Semaphore to control concurrency.
Integrates rate limiter and robots checker.
Reports progress via callback.
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, AsyncIterator, List, Dict, Optional
from datetime import datetime, timezone
import aiohttp

from techdetector.config import load_config
from techdetector.models import ScanResult, DetectionVector
from techdetector.storage import save_scan_result, get_company_detections
from techdetector.fetcher import fetch_domain_async
from techdetector.rate_limiter import RateLimiter
from techdetector.robots_parser import RobotsChecker
from techdetector.career_crawler import discover_career_pages
from techdetector.scanner import _load_signatures, _normalize_domain

from techdetector.detectors.html_detector import HtmlDetector
from techdetector.detectors.header_detector import HeaderDetector
from techdetector.detectors.dns_detector import DNSDetector
from techdetector.detectors.job_posting_detector import JobPostingDetector

logger = logging.getLogger(__name__)

@dataclass
class BatchConfig:
    max_concurrent: int = 10       # Max simultaneous domains
    max_per_domain: float = 2.0    # Requests/sec per domain
    respect_robots: bool = True
    skip_recent: bool = True       # Skip if scanned in last 24h
    recent_hours: int = 24
    retry_count: int = 3
    retry_delay: float = 5.0

@dataclass  
class ScanProgress:
    total: int
    completed: int
    successful: int
    failed: int
    skipped: int
    current_domain: str | None

async def perform_scan_async(
    session: aiohttp.ClientSession,
    domain: str,
    rate_limiter: RateLimiter,
    robots_checker: RobotsChecker,
    config: BatchConfig,
    signatures: List[Dict],
    active_vectors: List[str]
) -> tuple[bool, Optional[str]]:
    """Perform async scan of a single domain. Returns (success, error_msg)."""
    
    url = f"https://{domain}"
    
    if config.respect_robots:
        allowed, crawl_delay = await robots_checker.is_allowed(url)
        if not allowed:
            return False, "Disallowed by robots.txt"
        if crawl_delay is not None:
            await rate_limiter.update_from_robots(domain, crawl_delay)

    if config.skip_recent:
        # Check if company was recently scanned (simple check: if any detections in last recent_hours)
        existing = get_company_detections(domain)
        if existing:
            # Get latest scan date
            latest_date_str = max(d.get('last_verified_at', d.get('first_detected_at')) for d in existing)
            try:
                latest_date = datetime.fromisoformat(latest_date_str.replace('Z', '+00:00'))
                hours_diff = (datetime.now(timezone.utc) - latest_date).total_seconds() / 3600
                if hours_diff < config.recent_hours:
                    return True, "skipped_recent"
            except (ValueError, TypeError):
                pass
    
    all_detections = []
    html_fetched = False
    headers_captured = False

    if "html" in active_vectors or "headers" in active_vectors:
        fetch_result = await fetch_domain_async(session, url, rate_limiter)
        
        if fetch_result.error:
            return False, fetch_result.error
            
        html_fetched = fetch_result.html is not None
        headers_captured = bool(fetch_result.headers)

        if "html" in active_vectors and fetch_result.html:
            html_detector = HtmlDetector(signatures)
            all_detections.extend(html_detector.detect(fetch_result.html))
            
        if "headers" in active_vectors and fetch_result.headers:
            header_detector = HeaderDetector(signatures)
            all_detections.extend(header_detector.detect(fetch_result.headers))

    if "dns" in active_vectors:
        # DNS is pseudo-async here as dnspython defaults to sync unless we use async resolver.
        # Running in executor handles blocking.
        loop = asyncio.get_running_loop()
        dns_detector = DNSDetector(signatures)
        dns_results = await loop.run_in_executor(None, dns_detector.detect, domain)
        all_detections.extend(dns_results)

    if "job_posting" in active_vectors:
        # Also pseudo-async for existing crawler if it's sync. We will run it in executor.
        loop = asyncio.get_running_loop()
        career_res = await loop.run_in_executor(None, discover_career_pages, domain)
        if career_res.aggregated_text:
            job_detector = JobPostingDetector(signatures)
            job_results = job_detector.detect(career_res.aggregated_text)
            all_detections.extend(job_results)

    # Deduplicate
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

    try:
        save_scan_result(result)
        return True, None
    except Exception as e:
        return False, f"DB Error: {e}"

async def _worker(
    session: aiohttp.ClientSession,
    queue: asyncio.Queue,
    rate_limiter: RateLimiter,
    robots_checker: RobotsChecker,
    config: BatchConfig,
    signatures: List[Dict],
    active_vectors: List[str],
    progress: ScanProgress,
    progress_callback: Optional[Callable[[ScanProgress], None]]
):
    while True:
        try:
            domain = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        progress.current_domain = domain
        if progress_callback:
            progress_callback(progress)
            
        success = False
        error_msg = None
        
        for attempt in range(config.retry_count):
            try:
                success, error_msg = await perform_scan_async(
                    session, domain, rate_limiter, robots_checker, config, signatures, active_vectors
                )
                if success or error_msg == "Disallowed by robots.txt" or error_msg == "skipped_recent":
                    break
            except Exception as e:
                error_msg = str(e)
            
            if attempt < config.retry_count - 1 and not success:
                await asyncio.sleep(config.retry_delay)
                
        progress.completed += 1
        if success:
            if error_msg == "skipped_recent":
                progress.skipped += 1
            else:
                progress.successful += 1
        else:
            progress.failed += 1
            
        if progress_callback:
            progress_callback(progress)
            
        queue.task_done()


async def scan_batch(
    domains: List[str],
    config: BatchConfig,
    progress_callback: Callable[[ScanProgress], None] | None = None
) -> Dict:
    """
    Scan multiple domains concurrently with rate limiting.
    
    Returns summary dict with success/failure counts.
    """
    signatures = _load_signatures()
    active_vectors = ["html", "headers", "dns", "job_posting"]
    
    progress = ScanProgress(
        total=len(domains),
        completed=0,
        successful=0,
        failed=0,
        skipped=0,
        current_domain=None
    )
    
    if progress_callback:
        progress_callback(progress)
        
    rate_limiter = RateLimiter(default_rate=config.max_per_domain)
    robots_checker = RobotsChecker()
    
    queue = asyncio.Queue()
    for d in domains:
        queue.put_nowait(_normalize_domain(d))
        
    connector = aiohttp.TCPConnector(limit=config.max_concurrent * 2)
    async with aiohttp.ClientSession(connector=connector) as session:
        workers = []
        for _ in range(config.max_concurrent):
            w = asyncio.create_task(_worker(
                session, queue, rate_limiter, robots_checker, config, 
                signatures, active_vectors, progress, progress_callback
            ))
            workers.append(w)
            
        await asyncio.gather(*workers)
        
    return {
        "total": progress.total,
        "successful": progress.successful,
        "failed": progress.failed,
        "skipped": progress.skipped
    }

async def stream_domains(filepath: str) -> AsyncIterator[str]:
    """
    Stream domains from file (one per line).
    Handles large files without loading all into memory.
    """
    import aiofiles
    async with aiofiles.open(filepath, mode='r') as f:
        async for line in f:
            domain = line.strip()
            if domain and not domain.startswith("#"):
                yield domain
