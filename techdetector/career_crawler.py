"""
Discovers and fetches career/jobs pages for a domain.
"""
import logging
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from techdetector.fetcher import fetch_domain

logger = logging.getLogger(__name__)

@dataclass
class CareerPageResult:
    domain: str
    career_urls_found: list[str]
    aggregated_text: str
    job_postings_found: int

def discover_career_pages(domain: str) -> CareerPageResult:
    """Find and fetch text from career pages on a given domain."""
    logger.info(f"Discovering career pages for: {domain}")
    
    candidate_urls = [
        f"https://careers.{domain}",
        f"https://{domain}/careers",
        f"https://{domain}/jobs",
        f"https://jobs.{domain}",
        f"https://{domain}/about/careers",
        f"https://{domain}/company/careers"
    ]
    
    # Also fetch the main site to extract links pointing to jobs
    main_result = fetch_domain(domain)
    
    if main_result.html:
        soup = BeautifulSoup(main_result.html, 'html.parser')
        career_keywords = ['career', 'job', 'join our team', 'openings', 'work with us']
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().lower().strip()
            
            is_match = any(k in text for k in career_keywords) or any(k in href.lower() for k in ['career', 'job'])
            
            if is_match:
                full_url = urljoin(f"https://{domain}", href)
                # Ensure it's the same base domain
                if urlparse(full_url).netloc.endswith(domain) and full_url not in candidate_urls:
                    candidate_urls.append(full_url)

    urls_found = []
    texts = []
    
    for url in candidate_urls:
        if len(urls_found) >= 5: # Limit how many we crawl
            break
            
        res = fetch_domain(url)
        if res.status_code == 200 and res.html:
            urls_found.append(res.final_url)
            soup = BeautifulSoup(res.html, 'html.parser')
            # remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=' ')
            
            # Collapse whitespace
            import re
            text = re.sub(r'\s+', ' ', text)
            texts.append(text.strip())

    found = len(urls_found)
    agg_text = " ".join(texts)
    
    logger.info(f"Discovery complete for {domain}. Found {found} career pages.")
    
    return CareerPageResult(
        domain=domain,
        career_urls_found=urls_found,
        aggregated_text=agg_text,
        job_postings_found=found # We are just counting fetched pages as "postings" for simplicity right now
    )
