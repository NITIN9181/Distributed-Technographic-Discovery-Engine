// crawler/crates/crawler-core/src/main.rs
mod config;
mod dns_resolver;
mod error;
mod fetcher;
mod payload;
mod rate_limiter;
mod robots;
mod tls_inspector;
mod user_agent;

use config::CrawlerConfig;
use dns_resolver::DnsResolver;
use fetcher::Fetcher;
use rate_limiter::DistributedRateLimiter;
use robots::RobotsCache;
use tls_inspector::TlsInspector;

use crawler_kafka::producer::KafkaPayloadProducer;

use std::sync::Arc;
use tokio::sync::Semaphore;
use tracing::{info, error, warn};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize structured logging
    tracing_subscriber::fmt()
        .with_env_filter("crawler_core=debug,info")
        .json()
        .init();

    let config = Arc::new(CrawlerConfig::default());

    // Initialize subsystems
    let rate_limiter = Arc::new(DistributedRateLimiter::new(
        config.global_max_requests_per_second,
        config.max_requests_per_second_per_domain,
    ));

    let http_client = reqwest::Client::builder()
        .timeout(config.request_timeout)
        .build()?;

    let robots_cache = Arc::new(RobotsCache::new(
        config.robots_txt_cache_ttl,
        http_client.clone(),
    ));

    let fetcher = Arc::new(Fetcher::new(
        config.clone(),
        rate_limiter.clone(),
        robots_cache.clone(),
    )?);

    let dns_resolver = Arc::new(DnsResolver::new().await?);

    let kafka_producer = Arc::new(KafkaPayloadProducer::new(&config.kafka_brokers)?);

    // Concurrency control
    let semaphore = Arc::new(Semaphore::new(config.max_concurrent_connections));

    // Load domains from seed file or database
    let domains = load_seed_domains().await?;
    info!(count = domains.len(), "Loaded seed domains");

    let mut handles = Vec::new();

    for domain in domains {
        let permit = semaphore.clone().acquire_owned().await?;
        let fetcher = fetcher.clone();
        let dns_resolver = dns_resolver.clone();
        let kafka_producer = kafka_producer.clone();
        let config = config.clone();

        let handle = tokio::spawn(async move {
            let _permit = permit; // held until task completes

            // Phase 1: Fetch main page
            let main_url = format!("https://{}", &domain);
            match fetcher.fetch(&domain, &main_url).await {
                Ok(payload) => {
                    // Publish HTML payload
                    if let Err(e) = kafka_producer.send_crawl_payload(
                        &config.kafka_topic_html, &payload, &domain
                    ).await {
                        error!(domain = %domain, error = %e, "Failed to publish HTML payload");
                    }

                    // Publish headers as separate payload
                    if let Err(e) = kafka_producer.send_headers(
                        &config.kafka_topic_headers, &payload, &domain
                    ).await {
                        error!(domain = %domain, error = %e, "Failed to publish header payload");
                    }
                }
                Err(e) => {
                    warn!(domain = %domain, error = %e, "Failed to fetch main page");
                }
            }

            // Phase 2: DNS resolution
            if config.enable_dns_resolution {
                match dns_resolver.resolve_all(&domain).await {
                    Ok(dns_payload) => {
                        if let Err(e) = kafka_producer.send_dns(
                            &config.kafka_topic_dns, &dns_payload, &domain
                        ).await {
                            error!(domain = %domain, error = %e, "Failed to publish DNS payload");
                        }
                    }
                    Err(e) => {
                        warn!(domain = %domain, error = %e, "DNS resolution failed");
                    }
                }
            }

            // Phase 3: TLS inspection (blocking, run on spawn_blocking)
            if config.enable_tls_inspection {
                let tls_domain = domain.clone();
                let tls_result = tokio::task::spawn_blocking(move || {
                    TlsInspector::inspect(&tls_domain)
                }).await;

                match tls_result {
                    Ok(Ok(tls_payload)) => {
                        if let Err(e) = kafka_producer.send_tls(
                            &config.kafka_topic_tls, &tls_payload, &domain
                        ).await {
                            error!(domain = %domain, error = %e, "Failed to publish TLS payload");
                        }
                    }
                    _ => {
                        warn!(domain = %domain, "TLS inspection failed");
                    }
                }
            }

            // Phase 4: Careers page crawl for job postings
            if config.enable_careers_crawl {
                let careers_urls = vec![
                    format!("https://careers.{}", &domain),
                    format!("https://{}/careers", &domain),
                    format!("https://{}/jobs", &domain),
                    format!("https://jobs.{}", &domain),
                ];

                for careers_url in careers_urls {
                    match fetcher.fetch(&domain, &careers_url).await {
                        Ok(payload) if payload.http_status == 200 => {
                            if let Err(e) = kafka_producer.send_job_posting(
                                &config.kafka_topic_jobs, &payload, &domain
                            ).await {
                                error!(domain = %domain, error = %e, "Failed to publish job posting");
                            }
                            break; // found a valid careers page
                        }
                        _ => continue,
                    }
                }
            }

            info!(domain = %domain, "Crawl complete");
        });

        handles.push(handle);
    }

    // Await all tasks
    for handle in handles {
        if let Err(e) = handle.await {
            error!(error = %e, "Task panicked");
        }
    }

    info!("Crawl batch complete");
    Ok(())
}

async fn load_seed_domains() -> anyhow::Result<Vec<String>> {
    // In production, this would read from a database or file
    // For demo, use a seed file
    let content = tokio::fs::read_to_string("domains.txt").await?;
    Ok(content.lines().map(|l| l.trim().to_string()).filter(|l| !l.is_empty()).collect())
}
