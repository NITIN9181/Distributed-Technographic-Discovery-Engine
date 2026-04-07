// crawler/crates/crawler-core/src/config.rs
use serde::Deserialize;
use std::time::Duration;

#[derive(Debug, Clone, Deserialize)]
pub struct CrawlerConfig {
    pub max_concurrent_connections: usize,    // e.g., 5000
    pub request_timeout: Duration,            // e.g., 15s
    pub connect_timeout: Duration,            // e.g., 10s
    pub max_response_body_bytes: usize,       // e.g., 5MB
    pub dns_cache_ttl: Duration,              // e.g., 300s
    pub robots_txt_cache_ttl: Duration,       // e.g., 3600s
    pub default_crawl_delay_ms: u64,          // e.g., 1000
    pub max_requests_per_second_per_domain: u32,  // e.g., 2
    pub global_max_requests_per_second: u32,  // e.g., 2000
    pub kafka_brokers: String,
    pub kafka_topic_html: String,
    pub kafka_topic_headers: String,
    pub kafka_topic_dns: String,
    pub kafka_topic_tls: String,
    pub kafka_topic_jobs: String,
    pub user_agents: Vec<String>,
    pub enable_tls_inspection: bool,
    pub enable_dns_resolution: bool,
    pub enable_careers_crawl: bool,
}

impl Default for CrawlerConfig {
    fn default() -> Self {
        Self {
            max_concurrent_connections: 5000,
            request_timeout: Duration::from_secs(15),
            connect_timeout: Duration::from_secs(10),
            max_response_body_bytes: 5 * 1024 * 1024,
            dns_cache_ttl: Duration::from_secs(300),
            robots_txt_cache_ttl: Duration::from_secs(3600),
            default_crawl_delay_ms: 1000,
            max_requests_per_second_per_domain: 2,
            global_max_requests_per_second: 2000,
            kafka_brokers: "localhost:9092".to_string(),
            kafka_topic_html: "raw_html_payloads".to_string(),
            kafka_topic_headers: "http_headers".to_string(),
            kafka_topic_dns: "dns_records".to_string(),
            kafka_topic_tls: "tls_metadata".to_string(),
            kafka_topic_jobs: "job_postings_raw".to_string(),
            user_agents: vec![
                "Mozilla/5.0 (compatible; TechBot/1.0)".to_string(),
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36".to_string(),
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15".to_string(),
            ],
            enable_tls_inspection: true,
            enable_dns_resolution: true,
            enable_careers_crawl: true,
        }
    }
}
