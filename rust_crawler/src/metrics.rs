//! Prometheus metrics for the Rust crawler.
use lazy_static::lazy_static;
use prometheus::{Counter, Encoder, Gauge, Histogram, Registry, TextEncoder};

lazy_static! {
    pub static ref REGISTRY: Registry = Registry::new();
    pub static ref REQUESTS_TOTAL: Counter =
        Counter::new("crawler_requests_total", "Total HTTP requests made").unwrap();
    pub static ref REQUESTS_DURATION: Histogram =
        Histogram::with_opts(prometheus::HistogramOpts::new(
            "crawler_request_duration_seconds",
            "HTTP request duration in seconds"
        ))
        .unwrap();
    pub static ref ACTIVE_CONNECTIONS: Gauge = Gauge::new(
        "crawler_active_connections",
        "Currently active HTTP connections"
    )
    .unwrap();
    pub static ref DNS_LOOKUPS: Counter =
        Counter::new("crawler_dns_lookups_total", "Total DNS lookups performed").unwrap();
    pub static ref MESSAGES_PUBLISHED: Counter = Counter::new(
        "crawler_messages_published_total",
        "Messages published to Redis stream"
    )
    .unwrap();
    pub static ref PUBLISH_ERRORS: Counter = Counter::new(
        "crawler_publish_errors_total",
        "Failed publishes to Redis stream"
    )
    .unwrap();
    pub static ref DOMAINS_SKIPPED: Counter = Counter::new(
        "crawler_domains_skipped_total",
        "Domains skipped due to robots.txt"
    )
    .unwrap();
}

pub fn register_metrics() {
    REGISTRY.register(Box::new(REQUESTS_TOTAL.clone())).unwrap();
    REGISTRY
        .register(Box::new(REQUESTS_DURATION.clone()))
        .unwrap();
    REGISTRY
        .register(Box::new(ACTIVE_CONNECTIONS.clone()))
        .unwrap();
    REGISTRY.register(Box::new(DNS_LOOKUPS.clone())).unwrap();
    REGISTRY
        .register(Box::new(MESSAGES_PUBLISHED.clone()))
        .unwrap();
    REGISTRY.register(Box::new(PUBLISH_ERRORS.clone())).unwrap();
    REGISTRY
        .register(Box::new(DOMAINS_SKIPPED.clone()))
        .unwrap();
}

pub fn metrics_handler() -> String {
    let encoder = TextEncoder::new();
    let metric_families = REGISTRY.gather();
    let mut buffer = Vec::new();
    encoder.encode(&metric_families, &mut buffer).unwrap();
    String::from_utf8(buffer).unwrap()
}
