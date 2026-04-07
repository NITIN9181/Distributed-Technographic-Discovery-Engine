// crawler/crates/crawler-core/src/rate_limiter.rs
use dashmap::DashMap;
use governor::{Quota, RateLimiter as GovRateLimiter};
use governor::clock::DefaultClock;
use governor::state::{InMemoryState, NotKeyed};
use std::num::NonZeroU32;
use std::sync::Arc;
use tokio::time::Duration;

type DomainLimiter = GovRateLimiter<NotKeyed, InMemoryState, DefaultClock>;

pub struct DistributedRateLimiter {
    global_limiter: Arc<DomainLimiter>,
    per_domain_limiters: Arc<DashMap<String, Arc<DomainLimiter>>>,
    default_per_domain_rps: NonZeroU32,
}

impl DistributedRateLimiter {
    pub fn new(global_rps: u32, per_domain_rps: u32) -> Self {
        let global_quota = Quota::per_second(NonZeroU32::new(global_rps).unwrap());
        let global_limiter = Arc::new(GovRateLimiter::direct(global_quota));

        Self {
            global_limiter,
            per_domain_limiters: Arc::new(DashMap::new()),
            default_per_domain_rps: NonZeroU32::new(per_domain_rps).unwrap(),
        }
    }

    pub async fn acquire(&self, domain: &str) {
        // Wait for global rate limit
        self.global_limiter.until_ready().await;

        // Wait for per-domain rate limit
        let domain_limiter = self.per_domain_limiters
            .entry(domain.to_string())
            .or_insert_with(|| {
                let quota = Quota::per_second(self.default_per_domain_rps);
                Arc::new(GovRateLimiter::direct(quota))
            })
            .clone();

        domain_limiter.until_ready().await;
    }

    pub fn set_domain_rate(&self, domain: &str, rps: u32) {
        let quota = Quota::per_second(NonZeroU32::new(rps).unwrap());
        self.per_domain_limiters.insert(
            domain.to_string(),
            Arc::new(GovRateLimiter::direct(quota)),
        );
    }

    /// Periodically evict stale per-domain limiters to prevent memory leaks
    pub async fn cleanup_stale_entries(&self, max_entries: usize) {
        if self.per_domain_limiters.len() > max_entries {
            // Simple eviction: remove half the entries
            let keys: Vec<String> = self.per_domain_limiters
                .iter()
                .take(max_entries / 2)
                .map(|e| e.key().clone())
                .collect();
            for key in keys {
                self.per_domain_limiters.remove(&key);
            }
        }
    }
}
