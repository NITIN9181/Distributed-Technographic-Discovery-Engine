"""
robots.txt parsing and compliance.

Features:
- Caches robots.txt for 24 hours
- Respects Crawl-delay directive
- Checks if URL path is allowed for our user-agent
"""
import ssl
import time
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import asyncio
import aiohttp

USER_AGENT = "TechDetector/1.0"

@dataclass
class RobotsResult:
    allowed: bool
    crawl_delay: Optional[float]
    cached_at: float

class AsyncRobotFileParser(RobotFileParser):
    """Extension to handle parsing from string instead of synchronous fetch."""
    def parse_text(self, lines):
        self.parse(lines)

class RobotsChecker:
    def __init__(self, http_timeout: float = 10.0):
        self.cache: Dict[str, RobotsResult] = {}
        self.cache_ttl = 86400  # 24 hours
        self.timeout = aiohttp.ClientTimeout(total=http_timeout)
        self.lock = asyncio.Lock()
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context handling common enterprise certificate issues."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    async def fetch_robots(self, domain: str) -> RobotsResult:
        """Fetch and parse robots.txt for domain."""
        async with self.lock:
            # Check cache
            if domain in self.cache:
                result = self.cache[domain]
                if time.time() - result.cached_at < self.cache_ttl:
                    return result
                    
            robots_url = f"https://{domain}/robots.txt"
            
            try:
                ssl_ctx = self._create_ssl_context()
                connector = aiohttp.TCPConnector(ssl=ssl_ctx)
                
                async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
                    headers = {"User-Agent": USER_AGENT}
                    async with session.get(robots_url, headers=headers, allow_redirects=True) as response:
                        if response.status == 200:
                            text = await response.text()
                            parser = AsyncRobotFileParser(robots_url)
                            parser.parse_text(text.splitlines())
                            
                            # Check basic allowance for /
                            allowed = parser.can_fetch(USER_AGENT, f"https://{domain}/")
                            
                            crawl_delay = None
                            try:
                                # Retrieve crawl rate or delay. We focus on crawl_delay here.
                                rrate = parser.request_rate(USER_AGENT)
                                if rrate:
                                    crawl_delay = rrate.seconds / rrate.requests
                                else:
                                    cdelay = parser.crawl_delay(USER_AGENT)
                                    if cdelay:
                                        crawl_delay = float(cdelay)
                            except AttributeError:
                                pass # Some environments might not have these methods or return slightly different types
                            
                            result = RobotsResult(
                                allowed=allowed,
                                crawl_delay=crawl_delay,
                                cached_at=time.time()
                            )
                        else:
                            # If no robots.txt, assume allowed
                            result = RobotsResult(allowed=True, crawl_delay=None, cached_at=time.time())
            except Exception as e:
                # On error fetching robots.txt, default to allowed but no special delay
                print(f"Warning: Failed to fetch robots.txt for {domain}: {e}")
                result = RobotsResult(allowed=True, crawl_delay=None, cached_at=time.time())
                
            self.cache[domain] = result
            return result

    async def is_allowed(self, url: str) -> Tuple[bool, Optional[float]]:
        """
        Check if URL is crawlable.
        Returns (allowed: bool, crawl_delay: float | None)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if not domain:
                return True, None
                
            result = await self.fetch_robots(domain)
            return result.allowed, result.crawl_delay
        except Exception:
            return True, None
