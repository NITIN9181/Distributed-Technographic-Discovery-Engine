// =============================================================================
// Distributed Technographic Discovery Engine — Crawler Verification Script
// =============================================================================
//
// PURPOSE:
//   This is the Phase 0 "hello world" for the Rust crawler component.
//   It verifies that our async runtime (tokio) and HTTP client (reqwest)
//   are correctly configured by making a single GET request to httpbin.org.
//
// WHY ASYNC FROM THE START:
//   The full crawler will need to fetch thousands of pages concurrently.
//   Rust's async/await model (powered by tokio) lets us multiplex many
//   I/O-bound tasks onto a small thread pool. By starting with async now,
//   we avoid a painful rewrite later and ensure every abstraction we build
//   is concurrency-ready from day one.
//
// HOW THIS CONNECTS TO THE LARGER PROJECT:
//   - This `reqwest` client will evolve into the core fetching engine
//     with robots.txt compliance, rate limiting, and retry logic.
//   - The `tokio` runtime here will later drive concurrent crawl workers,
//     Kafka producers, and DNS/TLS inspection tasks.
//   - Response headers and TLS certificate data (accessible via reqwest)
//     are the raw signals we'll use for technology fingerprinting.
// =============================================================================

// `#[tokio::main]` is a procedural macro that transforms our `async fn main()`
// into a synchronous `fn main()` that boots up the tokio multi-threaded runtime
// and blocks on the async function. Without this, Rust has no built-in way to
// execute async code — we need an executor, and tokio is the gold standard.
#[tokio::main]
async fn main() {
    // Print a startup banner so we know the program is running.
    // In production, this becomes structured logging via `tracing`.
    println!("=================================================");
    println!("  Technographic Discovery Engine — Crawler v0.1  ");
    println!("  Phase 0: Environment Verification              ");
    println!("=================================================");
    println!();

    // --- Step 1: Build the HTTP client ---
    // `reqwest::Client::new()` creates a reusable HTTP client with:
    //   - Connection pooling (reuses TCP connections across requests)
    //   - TLS configuration (via rustls, as specified in Cargo.toml)
    //   - Default headers, redirect policy, and timeout settings
    //
    // In production, we'll configure this client with:
    //   - Custom User-Agent string identifying our crawler
    //   - Timeout limits to avoid hanging on slow servers
    //   - Redirect limits to prevent infinite redirect loops
    let client = reqwest::Client::new();

    // --- Step 2: Define the target URL ---
    // httpbin.org/get is a free HTTP testing service that echoes back
    // the request details (headers, IP, etc.) as JSON. It's perfect for
    // verifying our HTTP stack works end-to-end without hitting real sites.
    let url = "https://httpbin.org/get";

    println!("[INFO] Sending GET request to: {}", url);
    println!();

    // --- Step 3: Send the async GET request ---
    // `client.get(url).send().await` does the following:
    //   1. `.get(url)` — builds a GET request (doesn't send it yet)
    //   2. `.send()` — returns a Future representing the in-flight request
    //   3. `.await` — yields control to tokio's executor until the response
    //                  arrives, allowing other tasks to run concurrently
    //
    // This is the fundamental pattern for ALL our future crawling:
    // build a request, send it, await the response — but at scale with
    // thousands of these running concurrently via tokio::spawn().
    match client.get(url).send().await {
        // --- Success path ---
        Ok(response) => {
            // `response.status()` gives us the HTTP status code (e.g., 200 OK).
            // In the full crawler, we'll use this to:
            //   - Track success/failure rates per domain
            //   - Handle redirects (301/302) for URL canonicalization
            //   - Detect soft-404s and access restrictions (403/429)
            let status = response.status();
            println!("[SUCCESS] Response Status: {}", status);

            // `response.headers()` contains all HTTP response headers.
            // These are CRITICAL for technographic detection:
            //   - "Server" header reveals web server software (nginx, Apache, etc.)
            //   - "X-Powered-By" reveals backend frameworks (Express, PHP, etc.)
            //   - "Set-Cookie" patterns reveal session management tech
            //   - Custom headers (X-*) often fingerprint CDNs, WAFs, and platforms
            let headers = response.headers();
            println!("[INFO] Response Headers:");
            for (name, value) in headers.iter() {
                println!("  {}: {}", name, value.to_str().unwrap_or("<binary>"));
            }
            println!();

            // `response.content_length()` tells us the body size.
            // Useful for estimating bandwidth usage at scale.
            if let Some(len) = headers.get("content-length") {
                println!("[INFO] Content-Length: {} bytes", len.to_str().unwrap_or("unknown"));
            }

            // Read the response body as text.
            // In the full engine, we'd pass this HTML body to the Python
            // processor via Kafka for script tag extraction and analysis.
            match response.text().await {
                Ok(body) => {
                    // Show a preview of the response body (first 300 chars).
                    let preview_len = body.len().min(300);
                    println!("[INFO] Response Body Preview ({} bytes total):", body.len());
                    println!("  {}", &body[..preview_len]);
                    if body.len() > 300 {
                        println!("  ... [truncated]");
                    }
                }
                Err(e) => {
                    // Body read errors can happen if the connection drops mid-transfer.
                    // In production, we'd retry with exponential backoff.
                    eprintln!("[ERROR] Failed to read response body: {}", e);
                }
            }
        }
        // --- Error path ---
        Err(e) => {
            // Request errors include DNS failures, TLS errors, timeouts, etc.
            // Each error type gives us different technographic signals:
            //   - DNS failure → domain might be parked or expired
            //   - TLS error → interesting certificate info (self-signed, expired)
            //   - Timeout → server might be overloaded or rate-limiting us
            eprintln!("[ERROR] Request failed: {}", e);
            eprintln!();
            eprintln!("[HINT] Common causes:");
            eprintln!("  - No internet connection");
            eprintln!("  - Firewall blocking outbound HTTPS");
            eprintln!("  - DNS resolution failure");

            // Exit with a non-zero code to signal failure in CI/CD pipelines.
            std::process::exit(1);
        }
    }

    println!();
    println!("[DONE] Phase 0 verification complete!");
    println!("  ✓ Async runtime (tokio) is working");
    println!("  ✓ HTTP client (reqwest) is working");
    println!("  ✓ TLS (rustls) is working");
    println!("  → Ready to proceed to Phase 1: Core Crawler Implementation");
}
