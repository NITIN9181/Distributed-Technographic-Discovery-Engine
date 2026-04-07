// crawler/crates/crawler-core/src/fetcher.rs
use crate::config::CrawlerConfig;
use crate::payload::CrawlPayload;
use crate::rate_limiter::DistributedRateLimiter;
use crate::robots::RobotsCache;
use crate::user_agent::UserAgentRotator;
use chrono::Utc;
use reqwest::{Client, redirect::Policy, header};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;
use tracing::{debug, warn, error, instrument};
use url::Url;

pub struct Fetcher {
    client: Client,
    config: Arc<CrawlerConfig>,
    rate_limiter: Arc<DistributedRateLimiter>,
    robots_cache: Arc<RobotsCache>,
    ua_rotator: Arc<UserAgentRotator>,
}

impl Fetcher {
    pub fn new(
        config: Arc<CrawlerConfig>,
        rate_limiter: Arc<DistributedRateLimiter>,
        robots_cache: Arc<RobotsCache>,
    ) -> anyhow::Result<Self> {
        let client = Client::builder()
            .timeout(config.request_timeout)
            .connect_timeout(config.connect_timeout)
            .redirect(Policy::limited(5))
            .pool_max_idle_per_host(10)
            .pool_idle_timeout(std::time::Duration::from_secs(30))
            .tcp_nodelay(true)
            .gzip(true)
            .brotli(true)
            .deflate(true)
            .danger_accept_invalid_certs(false)
            .build()?;

        let ua_rotator = Arc::new(UserAgentRotator::new(config.user_agents.clone()));

        Ok(Self {
            client,
            config,
            rate_limiter,
            robots_cache,
            ua_rotator,
        })
    }

    #[instrument(skip(self), fields(domain = %domain))]
    pub async fn fetch(&self, domain: &str, url: &str) -> anyhow::Result<CrawlPayload> {
        // Parse URL to extract path for robots.txt check
        let parsed = Url::parse(url)?;
        let path = parsed.path();

        // Check robots.txt compliance
        let ua = self.ua_rotator.get();
        if !self.robots_cache.is_allowed(domain, path, ua).await {
            anyhow::bail!("Blocked by robots.txt: {} {}", domain, path);
        }

        // Respect crawl-delay from robots.txt
        if let Some(delay) = self.robots_cache.get_crawl_delay(domain).await {
            self.rate_limiter.set_domain_rate(
                domain,
                std::cmp::max(1, (1000 / delay.as_millis() as u32)),
            );
        }

        // Acquire rate limit token
        self.rate_limiter.acquire(domain).await;

        let start = Instant::now();

        let response = self.client
            .get(url)
            .header(header::USER_AGENT, ua)
            .header(header::ACCEPT, "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            .header(header::ACCEPT_LANGUAGE, "en-US,en;q=0.5")
            .header(header::ACCEPT_ENCODING, "gzip, deflate, br")
            .header(header::CONNECTION, "keep-alive")
            .send()
            .await?;

        let elapsed = start.elapsed().as_millis() as u64;
        let status = response.status().as_u16();
        let final_url = response.url().to_string();
        let content_type = response
            .headers()
            .get(header::CONTENT_TYPE)
            .and_then(|v| v.to_str().ok())
            .map(|s| s.to_string());

        // Capture all response headers
        let response_headers: HashMap<String, String> = response
            .headers()
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
            .collect();

        // Read body with size limit
        let body_bytes = response.bytes().await?;
        let html_body = if body_bytes.len() <= self.config.max_response_body_bytes {
            Some(String::from_utf8_lossy(&body_bytes).to_string())
        } else {
            warn!(domain = domain, size = body_bytes.len(), "Response body exceeds size limit, truncating");
            let truncated = &body_bytes[..self.config.max_response_body_bytes];
            Some(String::from_utf8_lossy(truncated).to_string())
        };

        Ok(CrawlPayload {
            canonical_domain: domain.to_string(),
            url: url.to_string(),
            crawl_timestamp: Utc::now(),
            html_body,
            http_status: status,
            response_headers,
            final_url,
            content_type,
            response_time_ms: elapsed,
        })
    }
}
