//! TechDetector Rust Crawler
//!
//! High-throughput async crawler that:
//! 1. Consumes domains from Redis queue
//! 2. Fetches HTML, headers, DNS, TLS for each
//! 3. Publishes results to Redis stream

mod dns;
mod fetcher;
mod metrics;
mod publisher;
mod rate_limiter;
mod robots;
mod tls;

use chrono::Utc;
use clap::Parser;
use redis::AsyncCommands;
use std::sync::Arc;
use tokio::sync::Semaphore;

#[derive(Parser)]
struct Config {
    /// Redis URL
    #[arg(long, env = "REDIS_URL", default_value = "redis://localhost:6379")]
    redis_url: String,

    /// Max concurrent requests
    #[arg(long, env = "MAX_CONCURRENT", default_value = "500")]
    max_concurrent: usize,

    /// Input queue name
    #[arg(long, default_value = "domains:pending")]
    input_queue: String,

    /// Output stream name  
    #[arg(long, default_value = "crawl:results")]
    output_stream: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    let config = Config::parse();

    let redis_client = redis::Client::open(config.redis_url.clone())?;

    let semaphore = Arc::new(Semaphore::new(config.max_concurrent));
    let fetcher = Arc::new(fetcher::Fetcher::new());
    let dns_resolver = Arc::new(dns::DNSResolver::new().await);
    let robots_cache = Arc::new(robots::RobotsCache::new());
    let rate_limiter = Arc::new(rate_limiter::DistributedRateLimiter::new(
        redis_client.clone(),
        2.0, // Default 2 req/sec
    ));
    let publisher = Arc::new(publisher::StreamPublisher::new(
        redis_client.clone(),
        config.output_stream.clone(),
    ));

    tracing::info!(
        "Starting Rust crawler with max concurrency {}",
        config.max_concurrent
    );

    // Register and start Prometheus metrics
    metrics::register_metrics();
    let metrics_port: u16 = std::env::var("METRICS_PORT")
        .unwrap_or_else(|_| "9090".to_string())
        .parse()
        .unwrap_or(9090);
    tokio::spawn(async move {
        use warp::Filter;
        let health =
            warp::path("health").map(|| warp::reply::with_status("OK", warp::http::StatusCode::OK));
        let metrics_route = warp::path("metrics").map(|| {
            warp::reply::with_header(
                metrics::metrics_handler(),
                "Content-Type",
                "text/plain; version=0.0.4",
            )
        });
        let routes = health.or(metrics_route);
        tracing::info!("Metrics server listening on port {}", metrics_port);
        warp::serve(routes).run(([0, 0, 0, 0], metrics_port)).await;
    });

    // Main loop: pop domain from queue, spawn crawl task
    loop {
        let mut con = match redis_client.get_async_connection().await {
            Ok(c) => c,
            Err(e) => {
                tracing::error!("Failed to connect to Redis: {}. Retrying...", e);
                tokio::time::sleep(std::time::Duration::from_secs(5)).await;
                continue;
            }
        };

        // Try to pop a domain
        let domain: Option<String> = match con.lpop(&config.input_queue, None).await {
            Ok(val) => val,
            Err(e) => {
                tracing::error!("Queue error: {}", e);
                tokio::time::sleep(std::time::Duration::from_secs(1)).await;
                continue;
            }
        };

        let domain = match domain {
            Some(d) => d,
            None => {
                // Queue empty, wait
                tokio::time::sleep(std::time::Duration::from_secs(2)).await;
                continue;
            }
        };

        let permit = semaphore.clone().acquire_owned().await.unwrap();

        let f_fetcher = fetcher.clone();
        let f_dns = dns_resolver.clone();
        let f_robots = robots_cache.clone();
        let f_limiter = rate_limiter.clone();
        let f_publisher = publisher.clone();

        tokio::spawn(async move {
            let _permit = permit;
            tracing::info!("Crawling domain: {}", domain);

            // 1. Robots.txt check
            let (allowed, delay) = f_robots.is_allowed(&domain, "/").await;
            if !allowed {
                tracing::warn!("Robots.txt disallowed crawling for {}", domain);
                metrics::DOMAINS_SKIPPED.inc();
                return;
            }

            if let Some(d) = delay {
                if let Err(e) = f_limiter.set_rate(&domain, 1.0 / d).await {
                    tracing::error!("Failed to set rate limit: {}", e);
                }
            }

            // 2. Wait for rate limit permit
            if let Err(e) = f_limiter.acquire(&domain).await {
                tracing::error!("Rate limit error for {}: {}", domain, e);
                return;
            }

            let main_url = format!("https://{}", domain);

            // 3. Concurrent fetches
            metrics::ACTIVE_CONNECTIONS.inc();
            let (fetch_res, career_res, dns_res, tls_res) = tokio::join!(
                f_fetcher.fetch(&main_url),
                f_fetcher.fetch_career_pages(&domain),
                f_dns.resolve(&domain),
                tls::extract_tls_info(&domain)
            );
            metrics::ACTIVE_CONNECTIONS.dec();
            metrics::REQUESTS_TOTAL.inc();
            metrics::DNS_LOOKUPS.inc();

            // 4. Publish result
            let result = publisher::CrawlResult {
                message_id: None,
                domain: domain.clone(),
                crawled_at: Utc::now().to_rfc3339(),
                html: fetch_res.html,
                headers: fetch_res.headers,
                career_pages: career_res,
                dns_records: dns_res,
                tls_info: tls_res,
            };

            match f_publisher.publish(result).await {
                Ok(msg_id) => {
                    metrics::MESSAGES_PUBLISHED.inc();
                    tracing::info!("Published result for {} (ID: {})", domain, msg_id);
                }
                Err(e) => {
                    metrics::PUBLISH_ERRORS.inc();
                    tracing::error!("Failed to publish result for {}: {}", domain, e);
                }
            }
        });
    }
}
