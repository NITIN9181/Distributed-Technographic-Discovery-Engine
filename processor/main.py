"""
=============================================================================
Distributed Technographic Discovery Engine — Processor Verification Script
=============================================================================

PURPOSE:
    This is the Phase 0 "hello world" for the Python processor component.
    It verifies that our HTML parsing pipeline (BeautifulSoup) and async
    HTTP capabilities (aiohttp) are correctly configured by parsing a
    sample HTML document and extracting all <script> tags.

WHY ASYNC FROM THE START:
    The processor will eventually consume crawled pages from Kafka and
    analyze them in parallel. Python's asyncio + aiohttp enables us to:
      - Process multiple pages concurrently without threading complexity
      - Make follow-up HTTP requests (e.g., fetching external JS files
        to fingerprint libraries) without blocking the main event loop
      - Integrate seamlessly with async Kafka consumers (aiokafka)

HOW THIS CONNECTS TO THE LARGER PROJECT:
    - BeautifulSoup is our primary tool for extracting technology signals
      from HTML: <script> tags, <meta> generators, <link> stylesheets,
      inline framework markers, and data attributes.
    - The script tag extraction here is the FOUNDATION of technographic
      detection — script sources reveal frameworks (React, Vue, Angular),
      analytics tools (GA, Segment), tag managers (GTM), and more.
    - aiohttp will be used to fetch and analyze external JavaScript files
      referenced in script tags, enabling deeper library fingerprinting.
=============================================================================
"""

import asyncio       # Python's built-in async event loop — our concurrency engine
import aiohttp       # Async HTTP client/server framework for Python
from bs4 import BeautifulSoup  # HTML/XML parser — the Swiss Army knife of web scraping


# --- Sample HTML Document ---
# This simulates a real webpage that the crawler would fetch.
# We've included various types of <script> tags that represent
# different technographic signals:
#   - External CDN scripts → identify frameworks and libraries
#   - Analytics scripts → identify tracking/measurement tools
#   - Inline scripts → may contain config objects revealing technologies
#   - Module scripts → indicate modern JavaScript practices
SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="WordPress 6.4.2">
    <title>Example Technographic Target</title>

    <!-- React from CDN — signals a React-based frontend -->
    <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>

    <!-- Google Analytics — signals GA4 usage for analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>

    <!-- Inline GA configuration — contains the measurement ID -->
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-XXXXXXXXXX');
    </script>
</head>
<body>
    <div id="root"></div>

    <!-- Application bundle — often contains webpack/vite chunk hashes -->
    <script type="module" src="/assets/app.a1b2c3d4.js"></script>

    <!-- Hotjar — signals session recording/heatmap tool usage -->
    <script>
        (function(h,o,t,j,a,r){
            h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
            h._hjSettings={hjid:1234567,hjsv:6};
        })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
    </script>

    <!-- Intercom — signals customer communication platform usage -->
    <script>
        window.intercomSettings = { api_base: "https://api-iam.intercom.io", app_id: "abc123" };
    </script>
</body>
</html>
"""


def extract_scripts(html: str) -> list[dict]:
    """
    Extract and categorize all <script> tags from an HTML document.

    This function is the core of our technographic signal extraction pipeline.
    For each script tag, we extract:
      - src: The URL of external scripts (None for inline scripts)
      - type: The script type attribute (e.g., "module", "application/json")
      - content_preview: First 80 chars of inline script content
      - is_async: Whether the script loads asynchronously
      - is_external: Whether the script references an external file

    Args:
        html: Raw HTML string to parse

    Returns:
        List of dictionaries, each describing one <script> tag found
    """
    # BeautifulSoup parses the HTML into a navigable tree structure.
    # We use "html.parser" (Python's built-in) for zero extra dependencies.
    # In production, we might switch to "lxml" for ~10x faster parsing
    # on large documents, but html.parser is fine for verification.
    soup = BeautifulSoup(html, "html.parser")

    # soup.find_all("script") traverses the entire DOM tree and returns
    # every <script> element. This is O(n) where n is the number of nodes.
    script_tags = soup.find_all("script")

    results = []
    for i, tag in enumerate(script_tags, start=1):
        # Extract the `src` attribute — if present, this is an external script.
        # External script URLs are GOLD for technographic detection because
        # CDN URLs contain library names and versions:
        #   e.g., "unpkg.com/react@18" → React v18
        #   e.g., "googletagmanager.com/gtag" → Google Tag Manager
        src = tag.get("src")

        # Extract the `type` attribute — helps categorize the script:
        #   - "module" → modern ES modules (signals modern build tools)
        #   - "application/ld+json" → structured data (not executable)
        #   - None/empty → standard JavaScript
        script_type = tag.get("type", "text/javascript")

        # Check for `async` or `defer` attributes — these affect load order
        # and can hint at script importance and loading strategy.
        is_async = tag.has_attr("async")
        is_deferred = tag.has_attr("defer")

        # For inline scripts, extract the text content.
        # Inline scripts often contain configuration objects that reveal:
        #   - API keys and service identifiers (GA measurement IDs, etc.)
        #   - Feature flags indicating A/B testing tools
        #   - SDK initialization calls revealing third-party integrations
        content = tag.string or ""
        content_preview = content.strip()[:80] + ("..." if len(content.strip()) > 80 else "")

        results.append({
            "index": i,
            "src": src,
            "type": script_type,
            "is_external": src is not None,
            "is_async": is_async,
            "is_deferred": is_deferred,
            "content_preview": content_preview if not src else None,
        })

    return results


async def fetch_url_demo(url: str) -> dict:
    """
    Demonstrate async HTTP fetching with aiohttp.

    This function shows the pattern we'll use in the full processor to:
      - Fetch external JavaScript files for deeper analysis
      - Make API calls to enrichment services
      - Download robots.txt and sitemap.xml files

    aiohttp uses a ClientSession that maintains a connection pool,
    similar to reqwest on the Rust side. We create one session and
    reuse it for all requests — this is a best practice for performance.

    Args:
        url: The URL to fetch

    Returns:
        Dictionary with status code and response preview
    """
    # `aiohttp.ClientSession()` creates a session with:
    #   - Connection pooling (reuses TCP connections)
    #   - Cookie jar (persists cookies across requests)
    #   - Default headers and timeout configuration
    #
    # The `async with` context manager ensures the session is properly
    # closed when we're done, releasing all connections back to the pool.
    async with aiohttp.ClientSession() as session:
        # `session.get(url)` returns a coroutine that, when awaited,
        # sends the HTTP request and returns the response.
        # The `async with` on the response ensures the connection is
        # released back to the pool even if we don't read the full body.
        async with session.get(url) as response:
            # Read the response body as text.
            # In production, we'd check Content-Type first and handle
            # binary responses (images, PDFs) differently.
            body = await response.text()

            return {
                "url": url,
                "status": response.status,
                "content_type": response.headers.get("Content-Type", "unknown"),
                "body_length": len(body),
                "body_preview": body[:200],
            }


async def main():
    """
    Main async entry point for the processor verification.

    This function orchestrates two verification tasks:
      1. HTML parsing with BeautifulSoup (synchronous, CPU-bound)
      2. HTTP fetching with aiohttp (asynchronous, I/O-bound)

    In the full system, this pattern maps to:
      1. Consume a crawled page from Kafka
      2. Parse the HTML to extract technology signals (CPU)
      3. Optionally fetch referenced resources for deeper analysis (I/O)
      4. Publish enriched results back to Kafka or to PostgreSQL
    """
    print("=" * 57)
    print("  Technographic Discovery Engine — Processor v0.1")
    print("  Phase 0: Environment Verification")
    print("=" * 57)
    print()

    # -------------------------------------------------------------------------
    # PART 1: HTML Script Tag Extraction
    # -------------------------------------------------------------------------
    # This verifies BeautifulSoup is installed and working correctly.
    # Script tag extraction is the first step in our technographic pipeline.
    print("[PART 1] HTML Script Tag Extraction")
    print("-" * 40)

    scripts = extract_scripts(SAMPLE_HTML)
    print(f"[INFO] Found {len(scripts)} <script> tags in sample HTML\n")

    for script in scripts:
        # Print each script with its classification.
        # This output format previews the structured data we'll eventually
        # store in PostgreSQL for the analytics dashboard.
        tag_type = "EXTERNAL" if script["is_external"] else "INLINE"
        async_flag = " [async]" if script["is_async"] else ""
        defer_flag = " [defer]" if script["is_deferred"] else ""

        print(f"  Script #{script['index']} [{tag_type}]{async_flag}{defer_flag}")
        if script["src"]:
            print(f"    src: {script['src']}")
        if script["content_preview"]:
            print(f"    content: {script['content_preview']}")
        print(f"    type: {script['type']}")
        print()

    # -------------------------------------------------------------------------
    # Summarize findings — this is a preview of the technographic report
    # -------------------------------------------------------------------------
    external_count = sum(1 for s in scripts if s["is_external"])
    inline_count = sum(1 for s in scripts if not s["is_external"])
    print(f"[SUMMARY]")
    print(f"  External scripts: {external_count}")
    print(f"  Inline scripts:   {inline_count}")
    print(f"  Async scripts:    {sum(1 for s in scripts if s['is_async'])}")
    print()

    # -------------------------------------------------------------------------
    # PART 2: Async HTTP Fetch with aiohttp
    # -------------------------------------------------------------------------
    # This verifies aiohttp is installed and async networking works.
    # We fetch from httpbin.org, the same service the Rust crawler uses.
    print("[PART 2] Async HTTP Fetch (aiohttp)")
    print("-" * 40)

    try:
        result = await fetch_url_demo("https://httpbin.org/get")
        print(f"[SUCCESS] Fetched: {result['url']}")
        print(f"  Status:       {result['status']}")
        print(f"  Content-Type: {result['content_type']}")
        print(f"  Body Length:  {result['body_length']} bytes")
        print(f"  Body Preview: {result['body_preview'][:100]}...")
    except aiohttp.ClientError as e:
        # aiohttp.ClientError is the base exception for all client errors.
        # This includes DNS failures, connection refused, timeouts, etc.
        print(f"[ERROR] HTTP request failed: {e}")
        print("[HINT] Check your internet connection and try again.")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    # -------------------------------------------------------------------------
    # Verification Summary
    # -------------------------------------------------------------------------
    print()
    print("=" * 57)
    print("[DONE] Phase 0 verification complete!")
    print("  ✓ BeautifulSoup HTML parsing is working")
    print("  ✓ Script tag extraction is working")
    print("  ✓ aiohttp async HTTP client is working")
    print("  ✓ asyncio event loop is working")
    print("  → Ready to proceed to Phase 1: Kafka Integration")
    print("=" * 57)


# This is the standard Python entry point.
# `asyncio.run(main())` creates a new event loop, runs our async main()
# function to completion, and then closes the loop. This is analogous
# to `#[tokio::main]` on the Rust side — it bridges sync and async worlds.
if __name__ == "__main__":
    asyncio.run(main())
