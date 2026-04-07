// crawler/crates/crawler-core/src/robots.rs
use dashmap::DashMap;
use reqwest::Client;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tracing::{debug, warn};

pub struct RobotsCache {
    cache: Arc<DashMap<String, CachedRobots>>,
    ttl: Duration,
    client: Client,
}

struct CachedRobots {
    rules: Option<robotstxt::Robots>,
    fetched_at: Instant,
    crawl_delay: Option<Duration>,
}

impl RobotsCache {
    pub fn new(ttl: Duration, client: Client) -> Self {
        Self {
            cache: Arc::new(DashMap::new()),
            ttl,
            client,
        }
    }

    pub async fn is_allowed(&self, domain: &str, path: &str, user_agent: &str) -> bool {
        let robots = self.get_or_fetch(domain).await;
        match robots {
            Some(r) => r.is_allowed(user_agent, path),
            None => true, // if robots.txt is unavailable, allow crawling
        }
    }

    pub async fn get_crawl_delay(&self, domain: &str) -> Option<Duration> {
        if let Some(entry) = self.cache.get(domain) {
            return entry.crawl_delay;
        }
        None
    }

    async fn get_or_fetch(&self, domain: &str) -> Option<robotstxt::Robots> {
        // Check cache validity
        if let Some(entry) = self.cache.get(domain) {
            if entry.fetched_at.elapsed() < self.ttl {
                return entry.rules.clone();
            }
        }

        // Fetch robots.txt
        let url = format!("https://{}/robots.txt", domain);
        match self.client.get(&url)
            .timeout(Duration::from_secs(10))
            .send()
            .await
        {
            Ok(response) if response.status().is_success() => {
                if let Ok(body) = response.text().await {
                    let robots = robotstxt::Robots::parse("*", &body);
                    let crawl_delay = Self::extract_crawl_delay(&body);
                    let cached = CachedRobots {
                        rules: Some(robots.clone()),
                        fetched_at: Instant::now(),
                        crawl_delay,
                    };
                    self.cache.insert(domain.to_string(), cached);
                    debug!(domain = domain, "robots.txt cached");
                    Some(robots)
                } else {
                    None
                }
            }
            _ => {
                // Cache the miss to avoid repeated requests
                self.cache.insert(domain.to_string(), CachedRobots {
                    rules: None,
                    fetched_at: Instant::now(),
                    crawl_delay: None,
                });
                warn!(domain = domain, "robots.txt not available");
                None
            }
        }
    }

    fn extract_crawl_delay(body: &str) -> Option<Duration> {
        for line in body.lines() {
            let trimmed = line.trim().to_lowercase();
            if trimmed.starts_with("crawl-delay:") {
                if let Some(val) = trimmed.strip_prefix("crawl-delay:") {
                    if let Ok(seconds) = val.trim().parse::<f64>() {
                        return Some(Duration::from_secs_f64(seconds));
                    }
                }
            }
        }
        None
    }
}
