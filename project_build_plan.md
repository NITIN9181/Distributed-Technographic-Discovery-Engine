Distributed Technographic Discovery Engine — Comprehensive Build Plan
Table of Contents
Project Overview & Architecture
Development Environment & Tooling Setup
Phase 1: Rust High-Throughput Async Crawler
Phase 2: Message Broker Integration
Phase 3: Python Processing Pipeline
Phase 4: NLP-Based Backend Technology Inference
Phase 5: PostgreSQL Data Layer
Phase 6: Orchestration, Deployment & Monitoring
Phase 7: Testing, Benchmarking & Hardening
Phase 8: Documentation & Portfolio Presentation
Detailed Timeline
Risk Register & Mitigations
1. Project Overview & Architecture
1.1 High-Level System Diagram
text

┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                                        │
│   ┌──────────────┐  ┌──────────────────┐  ┌────────────────────────────┐   │
│   │  Domain Feed  │  │  Scheduler /     │  │  Monitoring (Prometheus   │   │
│   │  (Seed URLs)  │  │  Rate Limiter    │  │  + Grafana)               │   │
│   └──────┬───────┘  └────────┬─────────┘  └────────────────────────────┘   │
│          │                   │                                              │
│          ▼                   ▼                                              │
│   ┌──────────────────────────────────────┐                                  │
│   │    RUST CRAWLER CLUSTER (Tokio)      │                                  │
│   │  ┌────────┐ ┌────────┐ ┌────────┐   │                                  │
│   │  │Worker 1│ │Worker 2│ │Worker N│   │                                  │
│   │  └───┬────┘ └───┬────┘ └───┬────┘   │                                  │
│   │      │          │          │         │                                  │
│   │  ┌───▼──────────▼──────────▼─────┐   │                                  │
│   │  │  Payload Assembler            │   │                                  │
│   │  │  (HTML + Headers + DNS + TLS) │   │                                  │
│   │  └──────────────┬────────────────┘   │                                  │
│   └─────────────────┼───────────────────┘                                  │
│                     │                                                       │
│                     ▼                                                       │
│   ┌─────────────────────────────────────┐                                   │
│   │   APACHE KAFKA / REDPANDA           │                                   │
│   │   Topics:                           │                                   │
│   │     • raw_html_payloads             │                                   │
│   │     • dns_records                   │                                   │
│   │     • http_headers                  │                                   │
│   │     • tls_metadata                  │                                   │
│   │     • job_postings_raw              │                                   │
│   └──────────────┬──────────────────────┘                                   │
│                  │                                                           │
│     ┌────────────┼────────────────────┐                                     │
│     ▼            ▼                    ▼                                     │
│  ┌──────────┐ ┌───────────┐ ┌──────────────────┐                           │
│  │Layer 1:  │ │Layer 2:   │ │Layer 3:          │                           │
│  │HTML      │ │HTTP Header│ │DNS Record        │                           │
│  │Analysis  │ │Inspection │ │Analysis          │                           │
│  │(Python)  │ │(Python)   │ │(Python)          │                           │
│  └────┬─────┘ └─────┬─────┘ └───────┬──────────┘                           │
│       │              │               │                                      │
│       │    ┌─────────▼───────────┐   │                                      │
│       │    │Layer 4:             │   │                                      │
│       │    │Job Posting NLP      │   │                                      │
│       │    │(SpaCy/Transformers) │   │                                      │
│       │    └─────────┬───────────┘   │                                      │
│       │              │               │                                      │
│       ▼              ▼               ▼                                      │
│   ┌──────────────────────────────────────┐                                  │
│   │   RESULT AGGREGATOR & DEDUPLICATOR   │                                  │
│   └──────────────────┬───────────────────┘                                  │
│                      ▼                                                      │
│   ┌──────────────────────────────────────┐                                  │
│   │   POSTGRESQL (TimescaleDB optional)  │                                  │
│   │   • scanned_companies                │                                  │
│   │   • technology_installations         │                                  │
│   └──────────────────────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
1.2 Component Responsibilities
Component	Language	Primary Responsibility
Async Crawler	Rust	Fetch HTML, HTTP headers, DNS records, TLS certs
Rate Limiter	Rust	Distributed token bucket, robots.txt compliance
Message Broker	Kafka/Redpanda	Decoupling ingestion from processing
HTML Analyzer	Python	Regex + AST-based tech fingerprinting
Header Inspector	Python	CDN, server, framework detection from headers
DNS Analyzer	Python	MX, SPF, TXT record tech inference
NLP Engine	Python	Named entity recognition on job postings
Data Store	PostgreSQL	Time-series technographic persistence
Orchestrator	Docker + K8s	Deployment, scaling, health checks
1.3 Repository Structure
text

technographic-engine/
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── .github/
│   └── workflows/
│       ├── rust-ci.yml
│       └── python-ci.yml
├── crawler/                          # Rust workspace
│   ├── Cargo.toml
│   ├── Cargo.lock
│   ├── crates/
│   │   ├── crawler-core/
│   │   │   ├── Cargo.toml
│   │   │   └── src/
│   │   │       ├── lib.rs
│   │   │       ├── main.rs
│   │   │       ├── config.rs
│   │   │       ├── fetcher.rs         # reqwest-based HTTP fetcher
│   │   │       ├── dns_resolver.rs    # trust-dns / hickory-dns
│   │   │       ├── tls_inspector.rs   # rustls certificate extraction
│   │   │       ├── robots.rs          # robots.txt parser + cache
│   │   │       ├── rate_limiter.rs    # distributed token bucket
│   │   │       ├── user_agent.rs      # UA rotation
│   │   │       ├── payload.rs         # CrawlPayload struct
│   │   │       └── error.rs
│   │   ├── crawler-kafka/
│   │   │   ├── Cargo.toml
│   │   │   └── src/
│   │   │       ├── lib.rs
│   │   │       └── producer.rs        # rdkafka producer
│   │   └── crawler-scheduler/
│   │       ├── Cargo.toml
│   │       └── src/
│   │           ├── lib.rs
│   │           └── scheduler.rs       # domain queue management
│   ├── tests/
│   │   ├── integration_tests.rs
│   │   └── fixtures/
│   └── Dockerfile
├── processor/                         # Python package
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                    # Kafka consumer entrypoint
│   │   ├── config.py
│   │   ├── consumers/
│   │   │   ├── __init__.py
│   │   │   ├── html_consumer.py
│   │   │   ├── header_consumer.py
│   │   │   ├── dns_consumer.py
│   │   │   └── job_posting_consumer.py
│   │   ├── detectors/
│   │   │   ├── __init__.py
│   │   │   ├── html_detector.py       # Layer 1
│   │   │   ├── header_detector.py     # Layer 2
│   │   │   ├── dns_detector.py        # Layer 3
│   │   │   └── nlp_detector.py        # Layer 4
│   │   ├── signatures/
│   │   │   ├── __init__.py
│   │   │   ├── technology_signatures.json
│   │   │   └── signature_loader.py
│   │   ├── nlp/
│   │   │   ├── __init__.py
│   │   │   ├── entity_recognizer.py
│   │   │   ├── technology_taxonomy.py
│   │   │   └── models/
│   │   ├── persistence/
│   │   │   ├── __init__.py
│   │   │   ├── db.py
│   │   │   ├── models.py
│   │   │   └── repository.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── deduplication.py
│   └── tests/
│       ├── test_html_detector.py
│       ├── test_header_detector.py
│       ├── test_dns_detector.py
│       ├── test_nlp_detector.py
│       └── fixtures/
├── database/
│   ├── migrations/
│   │   ├── 001_create_scanned_companies.sql
│   │   ├── 002_create_technology_installations.sql
│   │   ├── 003_create_indexes.sql
│   │   └── 004_create_hypertables.sql   # optional TimescaleDB
│   └── seed/
│       └── seed_domains.sql
├── infra/
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── crawler-deployment.yaml
│   │   ├── processor-deployment.yaml
│   │   ├── kafka-statefulset.yaml
│   │   ├── postgres-statefulset.yaml
│   │   └── monitoring/
│   │       ├── prometheus-config.yaml
│   │       └── grafana-dashboards.json
│   └── terraform/                      # optional cloud provisioning
├── scripts/
│   ├── seed_domains.py
│   ├── benchmark_crawler.py
│   └── generate_signature_db.py
└── docs/
    ├── architecture.md
    ├── api-reference.md
    ├── deployment-guide.md
    └── performance-benchmarks.md
2. Development Environment & Tooling Setup
2.1 Prerequisites Installation
Bash

# System-level dependencies (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    libpq-dev \
    cmake \
    protobuf-compiler \
    docker.io \
    docker-compose-plugin

# Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup default stable
rustup component add clippy rustfmt
cargo install cargo-watch cargo-nextest cargo-audit

# Python toolchain
sudo apt-get install -y python3.11 python3.11-venv python3-pip
pip install poetry  # or use uv for faster package management

# Database tools
sudo apt-get install -y postgresql-client-16

# Kafka CLI (optional, for debugging)
# Install via confluent-community package or use kcat
sudo apt-get install -y kafkacat
2.2 Local Development Stack via Docker Compose
YAML

# docker-compose.yml
version: '3.9'

services:
  redpanda:
    image: redpandadata/redpanda:v23.3.6
    command:
      - redpanda start
      - --smp 1
      - --memory 1G
      - --reserve-memory 0M
      - --overprovisioned
      - --node-id 0
      - --kafka-addr PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092
      - --advertise-kafka-addr PLAINTEXT://redpanda:29092,OUTSIDE://localhost:9092
    ports:
      - "9092:9092"
      - "8081:8081"    # Schema Registry
      - "8082:8082"    # REST Proxy
      - "9644:9644"    # Admin API
    volumes:
      - redpanda_data:/var/lib/redpanda/data

  redpanda-console:
    image: redpandadata/console:v2.3.8
    ports:
      - "8080:8080"
    environment:
      KAFKA_BROKERS: redpanda:29092
    depends_on:
      - redpanda

  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: technographics
      POSTGRES_USER: techuser
      POSTGRES_PASSWORD: techpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/migrations:/docker-entrypoint-initdb.d

  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@local.dev
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"

  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - ./infra/kubernetes/monitoring/prometheus-config.yaml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.2.0
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin

volumes:
  redpanda_data:
  postgres_data:
2.3 Topic Provisioning Script
Bash

#!/bin/bash
# scripts/create_topics.sh

BROKER="localhost:9092"

topics=(
  "raw_html_payloads:12:1"
  "http_headers:12:1"
  "dns_records:12:1"
  "tls_metadata:6:1"
  "job_postings_raw:6:1"
  "detected_technologies:12:1"
  "crawl_failures:6:1"
)

for topic_config in "${topics[@]}"; do
  IFS=':' read -r name partitions replication <<< "$topic_config"
  rpk topic create "$name" \
    --brokers "$BROKER" \
    --partitions "$partitions" \
    --replicas "$replication" \
    --topic-config retention.ms=604800000 \
    --topic-config compression.type=zstd
done
3. Phase 1: Rust High-Throughput Async Crawler
3.1 Workspace Configuration
toml

# crawler/Cargo.toml
[workspace]
members = [
    "crates/crawler-core",
    "crates/crawler-kafka",
    "crates/crawler-scheduler",
]
resolver = "2"

[workspace.dependencies]
tokio = { version = "1.35", features = ["full"] }
reqwest = { version = "0.11", features = ["json", "gzip", "brotli", "deflate", "rustls-tls"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["json", "env-filter"] }
thiserror = "1.0"
anyhow = "1.0"
rdkafka = { version = "0.36", features = ["cmake-build"] }
hickory-resolver = "0.24"
url = "2.5"
bytes = "1.5"
dashmap = "5.5"
governor = "0.6"     # rate limiting
rand = "0.8"
chrono = "0.4"
rustls = "0.22"
x509-parser = "0.16"
toml

# crawler/crates/crawler-core/Cargo.toml
[package]
name = "crawler-core"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio.workspace = true
reqwest.workspace = true
serde.workspace = true
serde_json.workspace = true
tracing.workspace = true
tracing-subscriber.workspace = true
thiserror.workspace = true
anyhow.workspace = true
hickory-resolver.workspace = true
url.workspace = true
bytes.workspace = true
dashmap.workspace = true
governor.workspace = true
rand.workspace = true
chrono.workspace = true
rustls.workspace = true
x509-parser.workspace = true
crawler-kafka = { path = "../crawler-kafka" }
crawler-scheduler = { path = "../crawler-scheduler" }
robotstxt = "0.3"
3.2 Configuration Module
Rust

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
3.3 Payload Data Structures
Rust

// crawler/crates/crawler-core/src/payload.rs
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawlPayload {
    pub canonical_domain: String,
    pub url: String,
    pub crawl_timestamp: DateTime<Utc>,
    pub html_body: Option<String>,
    pub http_status: u16,
    pub response_headers: HashMap<String, String>,
    pub final_url: String,  // after redirects
    pub content_type: Option<String>,
    pub response_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DnsPayload {
    pub canonical_domain: String,
    pub crawl_timestamp: DateTime<Utc>,
    pub a_records: Vec<String>,
    pub aaaa_records: Vec<String>,
    pub mx_records: Vec<MxRecord>,
    pub txt_records: Vec<String>,
    pub cname_records: Vec<String>,
    pub ns_records: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MxRecord {
    pub preference: u16,
    pub exchange: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TlsPayload {
    pub canonical_domain: String,
    pub crawl_timestamp: DateTime<Utc>,
    pub issuer: Option<String>,
    pub subject: Option<String>,
    pub serial_number: Option<String>,
    pub not_before: Option<String>,
    pub not_after: Option<String>,
    pub san_domains: Vec<String>,
    pub signature_algorithm: Option<String>,
    pub protocol_version: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobPostingPayload {
    pub canonical_domain: String,
    pub crawl_timestamp: DateTime<Utc>,
    pub page_url: String,
    pub raw_text: String,
    pub job_title: Option<String>,
}
3.4 Robots.txt Parser & Cache
Rust

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
3.5 Distributed Token Bucket Rate Limiter
Rust

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
3.6 User-Agent Rotation
Rust

// crawler/crates/crawler-core/src/user_agent.rs
use rand::seq::SliceRandom;
use rand::thread_rng;

pub struct UserAgentRotator {
    agents: Vec<String>,
}

impl UserAgentRotator {
    pub fn new(agents: Vec<String>) -> Self {
        assert!(!agents.is_empty(), "At least one user-agent required");
        Self { agents }
    }

    pub fn get(&self) -> &str {
        let mut rng = thread_rng();
        self.agents.choose(&mut rng).unwrap()
    }
}
3.7 DNS Resolver
Rust

// crawler/crates/crawler-core/src/dns_resolver.rs
use hickory_resolver::TokioAsyncResolver;
use hickory_resolver::config::*;
use crate::payload::{DnsPayload, MxRecord};
use chrono::Utc;
use tracing::{debug, error};

pub struct DnsResolver {
    resolver: TokioAsyncResolver,
}

impl DnsResolver {
    pub async fn new() -> anyhow::Result<Self> {
        let resolver = TokioAsyncResolver::tokio(
            ResolverConfig::default(),
            ResolverOpts {
                cache_size: 1024,
                use_hosts_file: false,
                ..Default::default()
            },
        );
        Ok(Self { resolver })
    }

    pub async fn resolve_all(&self, domain: &str) -> anyhow::Result<DnsPayload> {
        let mut payload = DnsPayload {
            canonical_domain: domain.to_string(),
            crawl_timestamp: Utc::now(),
            a_records: vec![],
            aaaa_records: vec![],
            mx_records: vec![],
            txt_records: vec![],
            cname_records: vec![],
            ns_records: vec![],
        };

        // A records
        if let Ok(response) = self.resolver.ipv4_lookup(domain).await {
            payload.a_records = response.iter().map(|r| r.to_string()).collect();
        }

        // AAAA records
        if let Ok(response) = self.resolver.ipv6_lookup(domain).await {
            payload.aaaa_records = response.iter().map(|r| r.to_string()).collect();
        }

        // MX records
        if let Ok(response) = self.resolver.mx_lookup(domain).await {
            payload.mx_records = response.iter().map(|r| MxRecord {
                preference: r.preference(),
                exchange: r.exchange().to_string(),
            }).collect();
        }

        // TXT records (critical for SPF/DKIM detection)
        if let Ok(response) = self.resolver.txt_lookup(domain).await {
            payload.txt_records = response.iter().map(|r| {
                r.iter()
                    .map(|data| String::from_utf8_lossy(data).to_string())
                    .collect::<Vec<_>>()
                    .join("")
            }).collect();
        }

        // NS records
        if let Ok(response) = self.resolver.ns_lookup(domain).await {
            payload.ns_records = response.iter().map(|r| r.to_string()).collect();
        }

        debug!(domain = domain, "DNS resolution complete");
        Ok(payload)
    }
}
3.8 TLS Certificate Inspector
Rust

// crawler/crates/crawler-core/src/tls_inspector.rs
use crate::payload::TlsPayload;
use chrono::Utc;
use rustls::{ClientConfig, ClientConnection, ServerName};
use std::io::{Read, Write};
use std::net::TcpStream;
use std::sync::Arc;
use x509_parser::prelude::*;
use tracing::{debug, warn};

pub struct TlsInspector;

impl TlsInspector {
    pub fn inspect(domain: &str) -> anyhow::Result<TlsPayload> {
        let mut root_store = rustls::RootCertStore::empty();
        root_store.add_trust_anchors(
            webpki_roots::TLS_SERVER_ROOTS.iter().map(|ta| {
                rustls::OwnedTrustAnchor::from_subject_spki_name_constraints(
                    ta.subject,
                    ta.spki,
                    ta.name_constraints,
                )
            })
        );

        let config = ClientConfig::builder()
            .with_safe_defaults()
            .with_root_certificates(root_store)
            .with_no_client_auth();

        let server_name = ServerName::try_from(domain)?;
        let mut conn = ClientConnection::new(Arc::new(config), server_name)?;
        let mut tcp = TcpStream::connect(format!("{}:443", domain))?;

        // Complete TLS handshake
        let mut stream = rustls::Stream::new(&mut conn, &mut tcp);
        stream.write_all(b"")?; // trigger handshake

        let mut payload = TlsPayload {
            canonical_domain: domain.to_string(),
            crawl_timestamp: Utc::now(),
            issuer: None,
            subject: None,
            serial_number: None,
            not_before: None,
            not_after: None,
            san_domains: vec![],
            signature_algorithm: None,
            protocol_version: None,
        };

        if let Some(certs) = conn.peer_certificates() {
            if let Some(cert_der) = certs.first() {
                if let Ok((_, cert)) = X509Certificate::from_der(cert_der.as_ref()) {
                    payload.issuer = Some(cert.issuer().to_string());
                    payload.subject = Some(cert.subject().to_string());
                    payload.serial_number = Some(cert.serial.to_str_radix(16));
                    payload.not_before = Some(cert.validity().not_before.to_rfc2822());
                    payload.not_after = Some(cert.validity().not_after.to_rfc2822());
                    payload.signature_algorithm = Some(
                        cert.signature_algorithm.algorithm.to_string()
                    );

                    // Extract SANs
                    if let Ok(Some(san_ext)) = cert.subject_alternative_name() {
                        for name in &san_ext.value.general_names {
                            if let GeneralName::DNSName(dns) = name {
                                payload.san_domains.push(dns.to_string());
                            }
                        }
                    }
                }
            }
        }

        if let Some(version) = conn.protocol_version() {
            payload.protocol_version = Some(format!("{:?}", version));
        }

        debug!(domain = domain, "TLS inspection complete");
        Ok(payload)
    }
}
3.9 Core Fetcher Engine
Rust

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
3.10 Main Orchestrator
Rust

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
                        &config.kafka_topic_html, &payload
                    ).await {
                        error!(domain = %domain, error = %e, "Failed to publish HTML payload");
                    }

                    // Publish headers as separate payload
                    if let Err(e) = kafka_producer.send_headers(
                        &config.kafka_topic_headers, &payload
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
                            &config.kafka_topic_dns, &dns_payload
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
                            &config.kafka_topic_tls, &tls_payload
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
                                &config.kafka_topic_jobs, &payload
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
3.11 Kafka Producer (Rust)
Rust

// crawler/crates/crawler-kafka/src/producer.rs
use rdkafka::config::ClientConfig;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::util::Timeout;
use crate::payload::*;
use serde::Serialize;
use std::time::Duration;
use tracing::error;

pub struct KafkaPayloadProducer {
    producer: FutureProducer,
}

impl KafkaPayloadProducer {
    pub fn new(brokers: &str) -> anyhow::Result<Self> {
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("message.timeout.ms", "5000")
            .set("queue.buffering.max.messages", "100000")
            .set("queue.buffering.max.kbytes", "1048576") // 1GB buffer
            .set("batch.num.messages", "1000")
            .set("linger.ms", "50")
            .set("compression.type", "zstd")
            .set("acks", "1")
            .create()?;

        Ok(Self { producer })
    }

    async fn send<T: Serialize>(&self, topic: &str, key: &str, payload: &T) -> anyhow::Result<()> {
        let json = serde_json::to_string(payload)?;
        let record = FutureRecord::to(topic)
            .key(key)
            .payload(&json);

        self.producer
            .send(record, Timeout::After(Duration::from_secs(5)))
            .await
            .map_err(|(err, _)| {
                error!(topic = topic, key = key, error = %err, "Kafka send failed");
                anyhow::anyhow!("Kafka produce error: {}", err)
            })?;

        Ok(())
    }

    pub async fn send_crawl_payload(&self, topic: &str, payload: &CrawlPayload) -> anyhow::Result<()> {
        self.send(topic, &payload.canonical_domain, payload).await
    }

    pub async fn send_headers(&self, topic: &str, payload: &CrawlPayload) -> anyhow::Result<()> {
        // Send just the header subset
        self.send(topic, &payload.canonical_domain, payload).await
    }

    pub async fn send_dns(&self, topic: &str, payload: &DnsPayload) -> anyhow::Result<()> {
        self.send(topic, &payload.canonical_domain, payload).await
    }

    pub async fn send_tls(&self, topic: &str, payload: &TlsPayload) -> anyhow::Result<()> {
        self.send(topic, &payload.canonical_domain, payload).await
    }

    pub async fn send_job_posting(&self, topic: &str, payload: &CrawlPayload) -> anyhow::Result<()> {
        self.send(topic, &payload.canonical_domain, payload).await
    }
}
4. Phase 2: Message Broker Integration
4.1 Topic Architecture
text

Topic: raw_html_payloads
  Partitions: 12 (keyed by domain for ordering)
  Retention: 7 days
  Compression: zstd
  Consumer Group: html-processors

Topic: http_headers
  Partitions: 12
  Retention: 7 days
  Consumer Group: header-processors

Topic: dns_records
  Partitions: 12
  Retention: 7 days
  Consumer Group: dns-processors

Topic: tls_metadata
  Partitions: 6
  Retention: 7 days
  Consumer Group: tls-processors

Topic: job_postings_raw
  Partitions: 6
  Retention: 14 days (NLP is slower, need buffer)
  Consumer Group: nlp-processors

Topic: detected_technologies (output)
  Partitions: 12
  Retention: 30 days
  Consumer Group: db-writers

Topic: crawl_failures (dead letter)
  Partitions: 6
  Retention: 30 days
4.2 Schema Registry (Avro/JSON Schema)
JSON

// schemas/crawl_payload.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CrawlPayload",
  "type": "object",
  "required": ["canonical_domain", "url", "crawl_timestamp", "http_status"],
  "properties": {
    "canonical_domain": { "type": "string" },
    "url": { "type": "string", "format": "uri" },
    "crawl_timestamp": { "type": "string", "format": "date-time" },
    "html_body": { "type": ["string", "null"] },
    "http_status": { "type": "integer" },
    "response_headers": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    },
    "final_url": { "type": "string" },
    "content_type": { "type": ["string", "null"] },
    "response_time_ms": { "type": "integer" }
  }
}
5. Phase 3: Python Processing Pipeline
5.1 Project Configuration
toml

# processor/pyproject.toml
[project]
name = "technographic-processor"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "confluent-kafka>=2.3.0",
    "psycopg2-binary>=2.9.9",
    "sqlalchemy>=2.0.23",
    "spacy>=3.7.2",
    "beautifulsoup4>=4.12.2",
    "lxml>=4.9.4",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "structlog>=23.2.0",
    "prometheus-client>=0.19.0",
    "orjson>=3.9.10",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=23.12.0",
    "ruff>=0.1.8",
    "mypy>=1.7.1",
]
5.2 Configuration
Python

# processor/src/config.py
from pydantic_settings import BaseSettings
from typing import List

class ProcessorConfig(BaseSettings):
    # Kafka
    kafka_brokers: str = "localhost:9092"
    kafka_consumer_group_html: str = "html-processors"
    kafka_consumer_group_headers: str = "header-processors"
    kafka_consumer_group_dns: str = "dns-processors"
    kafka_consumer_group_nlp: str = "nlp-processors"
    kafka_topic_html: str = "raw_html_payloads"
    kafka_topic_headers: str = "http_headers"
    kafka_topic_dns: str = "dns_records"
    kafka_topic_tls: str = "tls_metadata"
    kafka_topic_jobs: str = "job_postings_raw"
    kafka_topic_output: str = "detected_technologies"

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "technographics"
    db_user: str = "techuser"
    db_password: str = "techpass"

    # NLP
    spacy_model: str = "en_core_web_lg"

    # Processing
    batch_size: int = 100
    commit_interval_seconds: int = 5

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_prefix = "TECHNO_"
5.3 Technology Signature Database
JSON

// processor/src/signatures/technology_signatures.json
{
  "html_signatures": [
    {
      "technology": "Google Analytics",
      "category": "Analytics",
      "patterns": [
        {"type": "script_src", "regex": "google-analytics\\.com/analytics\\.js"},
        {"type": "script_src", "regex": "googletagmanager\\.com/gtag/js"},
        {"type": "html_content", "regex": "UA-\\d{4,10}-\\d{1,4}"},
        {"type": "html_content", "regex": "G-[A-Z0-9]{10,}"},
        {"type": "script_src", "regex": "google-analytics\\.com/ga\\.js"}
      ]
    },
    {
      "technology": "Google Tag Manager",
      "category": "Tag Management",
      "patterns": [
        {"type": "script_src", "regex": "googletagmanager\\.com/gtm\\.js"},
        {"type": "html_content", "regex": "GTM-[A-Z0-9]{6,}"}
      ]
    },
    {
      "technology": "HubSpot",
      "category": "Marketing Automation",
      "patterns": [
        {"type": "script_src", "regex": "js\\.hs-scripts\\.com"},
        {"type": "script_src", "regex": "js\\.hubspot\\.com"},
        {"type": "html_content", "regex": "hbspt\\.forms\\.create"},
        {"type": "meta_tag", "name": "generator", "regex": "HubSpot"}
      ]
    },
    {
      "technology": "Intercom",
      "category": "Customer Messaging",
      "patterns": [
        {"type": "script_src", "regex": "widget\\.intercom\\.io"},
        {"type": "html_content", "regex": "intercomSettings"},
        {"type": "html_content", "regex": "Intercom\\('boot'"}
      ]
    },
    {
      "technology": "Salesforce Pardot",
      "category": "Marketing Automation",
      "patterns": [
        {"type": "script_src", "regex": "pi\\.pardot\\.com"},
        {"type": "html_content", "regex": "piAId"},
        {"type": "html_content", "regex": "piCId"}
      ]
    },
    {
      "technology": "React",
      "category": "JavaScript Framework",
      "patterns": [
        {"type": "html_content", "regex": "data-reactroot"},
        {"type": "html_content", "regex": "data-reactid"},
        {"type": "html_content", "regex": "__NEXT_DATA__"},
        {"type": "script_src", "regex": "react(?:\\.production|\\.development)\\.min\\.js"}
      ]
    },
    {
      "technology": "Next.js",
      "category": "JavaScript Framework",
      "patterns": [
        {"type": "html_content", "regex": "__NEXT_DATA__"},
        {"type": "html_content", "regex": "_next/static"},
        {"type": "meta_tag", "name": "next-head-count", "regex": ".*"}
      ]
    },
    {
      "technology": "Vue.js",
      "category": "JavaScript Framework",
      "patterns": [
        {"type": "html_content", "regex": "data-v-[a-f0-9]{8}"},
        {"type": "script_src", "regex": "vue(?:\\.min)?\\.js"},
        {"type": "html_content", "regex": "__vue__"}
      ]
    },
    {
      "technology": "WordPress",
      "category": "CMS",
      "patterns": [
        {"type": "meta_tag", "name": "generator", "regex": "WordPress"},
        {"type": "html_content", "regex": "wp-content/"},
        {"type": "html_content", "regex": "wp-includes/"},
        {"type": "link_href", "regex": "/wp-json/"}
      ]
    },
    {
      "technology": "Shopify",
      "category": "E-Commerce",
      "patterns": [
        {"type": "html_content", "regex": "cdn\\.shopify\\.com"},
        {"type": "html_content", "regex": "Shopify\\.theme"},
        {"type": "meta_tag", "name": "shopify-digital-wallet", "regex": ".*"}
      ]
    },
    {
      "technology": "Stripe",
      "category": "Payment",
      "patterns": [
        {"type": "script_src", "regex": "js\\.stripe\\.com"},
        {"type": "html_content", "regex": "Stripe\\("},
        {"type": "html_content", "regex": "pk_live_[a-zA-Z0-9]+"}
      ]
    },
    {
      "technology": "Segment",
      "category": "Analytics",
      "patterns": [
        {"type": "script_src", "regex": "cdn\\.segment\\.com"},
        {"type": "html_content", "regex": "analytics\\.identify"},
        {"type": "html_content", "regex": "analytics\\.track"}
      ]
    },
    {
      "technology": "Drift",
      "category": "Conversational Marketing",
      "patterns": [
        {"type": "script_src", "regex": "js\\.driftt\\.com"},
        {"type": "html_content", "regex": "drift\\.load"}
      ]
    },
    {
      "technology": "Cloudflare",
      "category": "CDN/Security",
      "patterns": [
        {"type": "script_src", "regex": "cdnjs\\.cloudflare\\.com"},
        {"type": "html_content", "regex": "cf-browser-verification"},
        {"type": "html_content", "regex": "__cf_bm"}
      ]
    },
    {
      "technology": "Marketo",
      "category": "Marketing Automation",
      "patterns": [
        {"type": "script_src", "regex": "munchkin\\.marketo\\.net"},
        {"type": "html_content", "regex": "Munchkin\\.init"},
        {"type": "html_content", "regex": "mktoForm"}
      ]
    }
  ],
  "header_signatures": [
    {
      "technology": "Nginx",
      "category": "Web Server",
      "header": "server",
      "regex": "nginx"
    },
    {
      "technology": "Apache",
      "category": "Web Server",
      "header": "server",
      "regex": "Apache"
    },
    {
      "technology": "Cloudflare",
      "category": "CDN",
      "header": "server",
      "regex": "cloudflare"
    },
    {
      "technology": "Cloudflare",
      "category": "CDN",
      "header": "cf-ray",
      "regex": ".*"
    },
    {
      "technology": "Amazon CloudFront",
      "category": "CDN",
      "header": "x-amz-cf-id",
      "regex": ".*"
    },
    {
      "technology": "Amazon CloudFront",
      "category": "CDN",
      "header": "via",
      "regex": "CloudFront"
    },
    {
      "technology": "Fastly",
      "category": "CDN",
      "header": "x-served-by",
      "regex": "cache-"
    },
    {
      "technology": "Fastly",
      "category": "CDN",
      "header": "x-fastly-request-id",
      "regex": ".*"
    },
    {
      "technology": "Akamai",
      "category": "CDN",
      "header": "x-akamai-transformed",
      "regex": ".*"
    },
    {
      "technology": "Varnish",
      "category": "Cache",
      "header": "via",
      "regex": "varnish"
    },
    {
      "technology": "ASP.NET",
      "category": "Web Framework",
      "header": "x-powered-by",
      "regex": "ASP\\.NET"
    },
    {
      "technology": "PHP",
      "category": "Programming Language",
      "header": "x-powered-by",
      "regex": "PHP"
    },
    {
      "technology": "Express.js",
      "category": "Web Framework",
      "header": "x-powered-by",
      "regex": "Express"
    },
    {
      "technology": "Vercel",
      "category": "Hosting",
      "header": "x-vercel-id",
      "regex": ".*"
    },
    {
      "technology": "Netlify",
      "category": "Hosting",
      "header": "x-nf-request-id",
      "regex": ".*"
    },
    {
      "technology": "AWS",
      "category": "Cloud Provider",
      "header": "x-amzn-requestid",
      "regex": ".*"
    },
    {
      "technology": "Heroku",
      "category": "PaaS",
      "header": "via",
      "regex": "vegur"
    }
  ],
  "dns_signatures": {
    "mx_signatures": [
      {"technology": "Google Workspace", "pattern": "google\\.com$|googlemail\\.com$"},
      {"technology": "Microsoft 365", "pattern": "outlook\\.com$|microsoft\\.com$"},
      {"technology": "Zoho Mail", "pattern": "zoho\\.com$"},
      {"technology": "ProtonMail", "pattern": "protonmail\\.ch$"},
      {"technology": "Mimecast", "pattern": "mimecast\\.com$"},
      {"technology": "Barracuda", "pattern": "barracudanetworks\\.com$"}
    ],
    "spf_signatures": [
      {"technology": "SendGrid", "pattern": "sendgrid\\.net"},
      {"technology": "Mailchimp", "pattern": "mailchimp\\.com|mandrillapp\\.com"},
      {"technology": "Amazon SES", "pattern": "amazonses\\.com"},
      {"technology": "Mailgun", "pattern": "mailgun\\.org"},
      {"technology": "SparkPost", "pattern": "sparkpostmail\\.com"},
      {"technology": "Postmark", "pattern": "mtasv\\.net"},
      {"technology": "Salesforce", "pattern": "salesforce\\.com"},
      {"technology": "HubSpot", "pattern": "hubspot\\.com"},
      {"technology": "Zendesk", "pattern": "zendesk\\.com"},
      {"technology": "Freshdesk", "pattern": "freshdesk\\.com"}
    ],
    "ns_signatures": [
      {"technology": "Cloudflare DNS", "pattern": "cloudflare\\.com$"},
      {"technology": "AWS Route 53", "pattern": "awsdns"},
      {"technology": "Google Cloud DNS", "pattern": "googledomains\\.com$"},
      {"technology": "Azure DNS", "pattern": "azure-dns\\.com$"},
      {"technology": "DNSimple", "pattern": "dnsimple\\.com$"},
      {"technology": "NS1", "pattern": "nsone\\.net$"}
    ]
  }
}
5.4 Layer 1: HTML Source Code Analysis
Python

# processor/src/detectors/html_detector.py
import re
import json
import structlog
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

logger = structlog.get_logger()

@dataclass
class TechnologyDetection:
    technology_identifier: str
    category: str
    detection_vector: str
    confidence: float
    evidence: str

class HTMLTechnographicDetector:
    """Layer 1: Detect technologies from HTML source code analysis."""

    def __init__(self, signatures_path: Optional[str] = None):
        if signatures_path is None:
            signatures_path = str(
                Path(__file__).parent.parent / "signatures" / "technology_signatures.json"
            )
        with open(signatures_path, "r") as f:
            self.signatures = json.load(f)

        # Pre-compile all regex patterns for performance
        self._compiled_patterns = []
        for sig in self.signatures.get("html_signatures", []):
            compiled = {
                "technology": sig["technology"],
                "category": sig["category"],
                "patterns": []
            }
            for pattern in sig["patterns"]:
                compiled["patterns"].append({
                    "type": pattern["type"],
                    "regex": re.compile(pattern["regex"], re.IGNORECASE),
                    "name": pattern.get("name"),
                })
            self._compiled_patterns.append(compiled)

        logger.info("HTML detector initialized", signature_count=len(self._compiled_patterns))

    def detect(self, html: str, url: str) -> List[TechnologyDetection]:
        """Perform multi-method HTML analysis."""
        detections = []

        # Parse HTML with BeautifulSoup for structured analysis
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as e:
            logger.warning("HTML parsing failed, falling back to regex-only", error=str(e))
            soup = None

        for sig in self._compiled_patterns:
            for pattern in sig["patterns"]:
                detection = None

                if pattern["type"] == "script_src" and soup:
                    detection = self._check_script_sources(soup, sig, pattern)
                elif pattern["type"] == "html_content":
                    detection = self._check_raw_html(html, sig, pattern)
                elif pattern["type"] == "meta_tag" and soup:
                    detection = self._check_meta_tags(soup, sig, pattern)
                elif pattern["type"] == "link_href" and soup:
                    detection = self._check_link_hrefs(soup, sig, pattern)

                if detection and not self._is_duplicate(detections, detection):
                    detections.append(detection)

        logger.info(
            "HTML detection complete",
            url=url,
            technologies_found=len(detections),
            technologies=[d.technology_identifier for d in detections]
        )
        return detections

    def _check_script_sources(
        self, soup: BeautifulSoup, sig: dict, pattern: dict
    ) -> Optional[TechnologyDetection]:
        for script in soup.find_all("script", src=True):
            src = script.get("src", "")
            if pattern["regex"].search(src):
                return TechnologyDetection(
                    technology_identifier=sig["technology"],
                    category=sig["category"],
                    detection_vector="HTML_SCRIPT_SRC",
                    confidence=0.95,
                    evidence=f"Script src: {src[:200]}"
                )
        return None

    def _check_raw_html(
        self, html: str, sig: dict, pattern: dict
    ) -> Optional[TechnologyDetection]:
        match = pattern["regex"].search(html)
        if match:
            # Extract surrounding context for evidence
            start = max(0, match.start() - 30)
            end = min(len(html), match.end() + 30)
            context = html[start:end].replace("\n", " ").strip()
            return TechnologyDetection(
                technology_identifier=sig["technology"],
                category=sig["category"],
                detection_vector="HTML_CONTENT_MATCH",
                confidence=0.85,
                evidence=f"Content match: ...{context}..."
            )
        return None

    def _check_meta_tags(
        self, soup: BeautifulSoup, sig: dict, pattern: dict
    ) -> Optional[TechnologyDetection]:
        meta_name = pattern.get("name")
        if not meta_name:
            return None

        meta = soup.find("meta", attrs={"name": meta_name})
        if meta is None:
            meta = soup.find("meta", attrs={"property": meta_name})

        if meta:
            content = meta.get("content", "")
            if pattern["regex"].search(content):
                return TechnologyDetection(
                    technology_identifier=sig["technology"],
                    category=sig["category"],
                    detection_vector="HTML_META_TAG",
                    confidence=0.98,
                    evidence=f"Meta tag {meta_name}={content[:100]}"
                )
        return None

    def _check_link_hrefs(
        self, soup: BeautifulSoup, sig: dict, pattern: dict
    ) -> Optional[TechnologyDetection]:
        for link in soup.find_all("link", href=True):
            href = link.get("href", "")
            if pattern["regex"].search(href):
                return TechnologyDetection(
                    technology_identifier=sig["technology"],
                    category=sig["category"],
                    detection_vector="HTML_LINK_HREF",
                    confidence=0.90,
                    evidence=f"Link href: {href[:200]}"
                )
        return None

    @staticmethod
    def _is_duplicate(
        existing: List[TechnologyDetection], new: TechnologyDetection
    ) -> bool:
        return any(
            d.technology_identifier == new.technology_identifier
            for d in existing
        )
5.5 Layer 2: HTTP Header Inspection
Python

# processor/src/detectors/header_detector.py
import re
import json
import structlog
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

logger = structlog.get_logger()

class HeaderTechnographicDetector:
    """Layer 2: Detect technologies from HTTP response headers."""

    def __init__(self, signatures_path: Optional[str] = None):
        if signatures_path is None:
            signatures_path = str(
                Path(__file__).parent.parent / "signatures" / "technology_signatures.json"
            )
        with open(signatures_path, "r") as f:
            sigs = json.load(f)

        self._compiled_signatures = []
        for sig in sigs.get("header_signatures", []):
            self._compiled_signatures.append({
                "technology": sig["technology"],
                "category": sig["category"],
                "header": sig["header"].lower(),
                "regex": re.compile(sig["regex"], re.IGNORECASE),
            })

        logger.info("Header detector initialized", signature_count=len(self._compiled_signatures))

    def detect(self, headers: Dict[str, str], domain: str) -> List:
        """Analyze response headers for technology fingerprints."""
        from .html_detector import TechnologyDetection

        # Normalize header keys to lowercase
        normalized = {k.lower(): v for k, v in headers.items()}
        detections = []
        seen_techs = set()

        for sig in self._compiled_signatures:
            header_value = normalized.get(sig["header"])
            if header_value and sig["regex"].search(header_value):
                tech = sig["technology"]
                if tech not in seen_techs:
                    seen_techs.add(tech)
                    detections.append(TechnologyDetection(
                        technology_identifier=tech,
                        category=sig["category"],
                        detection_vector="HTTP_HEADER",
                        confidence=0.92,
                        evidence=f"{sig['header']}: {header_value[:200]}"
                    ))

        # Additional heuristic: check Set-Cookie for technology hints
        cookies = normalized.get("set-cookie", "")
        cookie_patterns = {
            "ASP.NET": r"ASP\.NET_SessionId",
            "PHP": r"PHPSESSID",
            "Java": r"JSESSIONID",
            "Rails": r"_session_id.*rack",
            "Django": r"csrftoken.*django|sessionid",
            "Laravel": r"laravel_session",
        }
        for tech, pattern in cookie_patterns.items():
            if tech not in seen_techs and re.search(pattern, cookies, re.IGNORECASE):
                seen_techs.add(tech)
                detections.append(TechnologyDetection(
                    technology_identifier=tech,
                    category="Web Framework / Language",
                    detection_vector="HTTP_HEADER_COOKIE",
                    confidence=0.80,
                    evidence=f"Set-Cookie pattern matched for {tech}"
                ))

        # Check X-Generator header
        generator = normalized.get("x-generator", "")
        if generator:
            detections.append(TechnologyDetection(
                technology_identifier=generator.split("/")[0].strip(),
                category="CMS / Generator",
                detection_vector="HTTP_HEADER",
                confidence=0.95,
                evidence=f"x-generator: {generator}"
            ))

        logger.info(
            "Header detection complete",
            domain=domain,
            technologies_found=len(detections)
        )
        return detections
5.6 Layer 3: DNS Record Analysis
Python

# processor/src/detectors/dns_detector.py
import re
import json
import structlog
from typing import List, Optional, Dict
from pathlib import Path

logger = structlog.get_logger()

class DNSTechnographicDetector:
    """Layer 3: Detect technologies from DNS records (MX, TXT/SPF, NS)."""

    def __init__(self, signatures_path: Optional[str] = None):
        if signatures_path is None:
            signatures_path = str(
                Path(__file__).parent.parent / "signatures" / "technology_signatures.json"
            )
        with open(signatures_path, "r") as f:
            sigs = json.load(f)

        dns_sigs = sigs.get("dns_signatures", {})

        self._mx_signatures = [
            {"technology": s["technology"], "regex": re.compile(s["pattern"], re.IGNORECASE)}
            for s in dns_sigs.get("mx_signatures", [])
        ]
        self._spf_signatures = [
            {"technology": s["technology"], "regex": re.compile(s["pattern"], re.IGNORECASE)}
            for s in dns_sigs.get("spf_signatures", [])
        ]
        self._ns_signatures = [
            {"technology": s["technology"], "regex": re.compile(s["pattern"], re.IGNORECASE)}
            for s in dns_sigs.get("ns_signatures", [])
        ]

        logger.info(
            "DNS detector initialized",
            mx_sigs=len(self._mx_signatures),
            spf_sigs=len(self._spf_signatures),
            ns_sigs=len(self._ns_signatures),
        )

    def detect(self, dns_payload: Dict, domain: str) -> List:
        """Analyze DNS records for technology signals."""
        from .html_detector import TechnologyDetection

        detections = []
        seen = set()

        # MX record analysis → email provider
        for mx in dns_payload.get("mx_records", []):
            exchange = mx.get("exchange", "")
            for sig in self._mx_signatures:
                if sig["regex"].search(exchange) and sig["technology"] not in seen:
                    seen.add(sig["technology"])
                    detections.append(TechnologyDetection(
                        technology_identifier=sig["technology"],
                        category="Email Provider",
                        detection_vector="DNS_MX_RECORD",
                        confidence=0.97,
                        evidence=f"MX record: {exchange}"
                    ))

        # TXT/SPF record analysis → email marketing and SaaS tools
        for txt in dns_payload.get("txt_records", []):
            # SPF records
            if "v=spf1" in txt.lower():
                for sig in self._spf_signatures:
                    if sig["regex"].search(txt) and sig["technology"] not in seen:
                        seen.add(sig["technology"])
                        detections.append(TechnologyDetection(
                            technology_identifier=sig["technology"],
                            category="Email Marketing / SaaS",
                            detection_vector="DNS_SPF_RECORD",
                            confidence=0.93,
                            evidence=f"SPF include: {txt[:200]}"
                        ))

            # DKIM verification records can also reveal tools
            if "dkim" in txt.lower():
                dkim_providers = {
                    "google": "Google Workspace",
                    "microsoft": "Microsoft 365",
                    "sendgrid": "SendGrid",
                    "mailchimp": "Mailchimp",
                }
                for keyword, tech in dkim_providers.items():
                    if keyword in txt.lower() and tech not in seen:
                        seen.add(tech)
                        detections.append(TechnologyDetection(
                            technology_identifier=tech,
                            category="Email Infrastructure",
                            detection_vector="DNS_DKIM_RECORD",
                            confidence=0.88,
                            evidence=f"DKIM: {txt[:200]}"
                        ))

        # NS record analysis → DNS/hosting provider
        for ns in dns_payload.get("ns_records", []):
            for sig in self._ns_signatures:
                if sig["regex"].search(ns) and sig["technology"] not in seen:
                    seen.add(sig["technology"])
                    detections.append(TechnologyDetection(
                        technology_identifier=sig["technology"],
                        category="DNS Provider",
                        detection_vector="DNS_NS_RECORD",
                        confidence=0.95,
                        evidence=f"NS record: {ns}"
                    ))

        # A record analysis → cloud provider via IP range (simplified)
        a_records = dns_payload.get("a_records", [])
        if a_records:
            # In production, you'd use IP-to-ASN mapping databases
            # This is a simplified demonstration
            pass

        logger.info(
            "DNS detection complete",
            domain=domain,
            technologies_found=len(detections)
        )
        return detections
5.7 Kafka Consumers
Python

# processor/src/consumers/html_consumer.py
import orjson
import structlog
from confluent_kafka import Consumer, KafkaException
from typing import Callable, List
from ..config import ProcessorConfig
from ..detectors.html_detector import HTMLTechnographicDetector, TechnologyDetection
from ..detectors.header_detector import HeaderTechnographicDetector
from ..persistence.repository import TechnographicRepository

logger = structlog.get_logger()

class HTMLPayloadConsumer:
    """Consumes raw HTML payloads and runs Layer 1 + Layer 2 detection."""

    def __init__(self, config: ProcessorConfig, repository: TechnographicRepository):
        self.config = config
        self.repository = repository
        self.html_detector = HTMLTechnographicDetector()
        self.header_detector = HeaderTechnographicDetector()

        self.consumer = Consumer({
            "bootstrap.servers": config.kafka_brokers,
            "group.id": config.kafka_consumer_group_html,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": "300000",
            "session.timeout.ms": "30000",
            "fetch.min.bytes": "1024",
            "fetch.wait.max.ms": "500",
        })
        self.consumer.subscribe([config.kafka_topic_html])

    def run(self):
        """Main consumer loop."""
        logger.info("HTML consumer started", topic=self.config.kafka_topic_html)
        batch: List[dict] = []

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    if batch:
                        self._process_batch(batch)
                        batch = []
                    continue

                if msg.error():
                    logger.error("Consumer error", error=str(msg.error()))
                    continue

                payload = orjson.loads(msg.value())
                batch.append(payload)

                if len(batch) >= self.config.batch_size:
                    self._process_batch(batch)
                    batch = []
                    self.consumer.commit(asynchronous=True)

        except KeyboardInterrupt:
            logger.info("Consumer shutting down")
        finally:
            if batch:
                self._process_batch(batch)
            self.consumer.close()

    def _process_batch(self, batch: List[dict]):
        all_detections = []

        for payload in batch:
            domain = payload.get("canonical_domain", "")
            url = payload.get("url", "")
            html_body = payload.get("html_body")
            headers = payload.get("response_headers", {})
            crawl_timestamp = payload.get("crawl_timestamp")

            detections = []

            # Layer 1: HTML analysis
            if html_body:
                html_detections = self.html_detector.detect(html_body, url)
                detections.extend(html_detections)

            # Layer 2: Header analysis
            if headers:
                header_detections = self.header_detector.detect(headers, domain)
                detections.extend(header_detections)

            # Enrich with domain and timestamp
            for d in detections:
                all_detections.append({
                    "canonical_domain": domain,
                    "technology_identifier": d.technology_identifier,
                    "detection_vector": d.detection_vector,
                    "confidence": d.confidence,
                    "crawl_timestamp": crawl_timestamp,
                })

            # Upsert company record
            self.repository.upsert_company(domain, crawl_timestamp)

        # Batch persist detections
        if all_detections:
            self.repository.batch_upsert_technologies(all_detections)
            logger.info(
                "Batch processed",
                batch_size=len(batch),
                total_detections=len(all_detections)
            )
Python

# processor/src/consumers/dns_consumer.py
import orjson
import structlog
from confluent_kafka import Consumer
from typing import List
from ..config import ProcessorConfig
from ..detectors.dns_detector import DNSTechnographicDetector
from ..persistence.repository import TechnographicRepository

logger = structlog.get_logger()

class DNSPayloadConsumer:
    """Consumes DNS payloads and runs Layer 3 detection."""

    def __init__(self, config: ProcessorConfig, repository: TechnographicRepository):
        self.config = config
        self.repository = repository
        self.dns_detector = DNSTechnographicDetector()

        self.consumer = Consumer({
            "bootstrap.servers": config.kafka_brokers,
            "group.id": config.kafka_consumer_group_dns,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self.consumer.subscribe([config.kafka_topic_dns])

    def run(self):
        logger.info("DNS consumer started", topic=self.config.kafka_topic_dns)
        batch = []

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    if batch:
                        self._process_batch(batch)
                        batch = []
                    continue

                if msg.error():
                    continue

                payload = orjson.loads(msg.value())
                batch.append(payload)

                if len(batch) >= self.config.batch_size:
                    self._process_batch(batch)
                    batch = []
                    self.consumer.commit(asynchronous=True)
        except KeyboardInterrupt:
            pass
        finally:
            if batch:
                self._process_batch(batch)
            self.consumer.close()

    def _process_batch(self, batch: List[dict]):
        all_detections = []

        for payload in batch:
            domain = payload.get("canonical_domain", "")
            timestamp = payload.get("crawl_timestamp")
            detections = self.dns_detector.detect(payload, domain)

            for d in detections:
                all_detections.append({
                    "canonical_domain": domain,
                    "technology_identifier": d.technology_identifier,
                    "detection_vector": d.detection_vector,
                    "confidence": d.confidence,
                    "crawl_timestamp": timestamp,
                })

        if all_detections:
            self.repository.batch_upsert_technologies(all_detections)
            logger.info("DNS batch processed", detections=len(all_detections))
6. Phase 4: NLP-Based Backend Technology Inference
6.1 Technology Taxonomy
Python

# processor/src/nlp/technology_taxonomy.py
"""
Curated taxonomy of technologies that appear in job postings.
These are technologies that have NO frontend footprint and can
only be discovered through job description analysis.
"""

BACKEND_TECHNOLOGY_TAXONOMY = {
    # Databases
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Cassandra", "DynamoDB",
        "Redis", "Elasticsearch", "Neo4j", "CockroachDB", "ScyllaDB",
        "ClickHouse", "TimescaleDB", "InfluxDB", "Couchbase", "MariaDB",
        "Oracle Database", "SQL Server", "Snowflake", "BigQuery",
        "Redshift", "Databricks", "Apache Druid", "Apache Pinot",
    ],
    # Data Engineering
    "data_engineering": [
        "Apache Spark", "Apache Kafka", "Apache Flink", "Apache Airflow",
        "dbt", "Dagster", "Prefect", "Luigi", "Apache Beam",
        "Apache NiFi", "Fivetran", "Stitch", "Airbyte", "Talend",
        "Informatica", "Apache Hive", "Apache Presto", "Trino",
    ],
    # Infrastructure & DevOps
    "infrastructure": [
        "Kubernetes", "Docker", "Terraform", "Ansible", "Puppet",
        "Chef", "Pulumi", "AWS CDK", "CloudFormation", "Helm",
        "ArgoCD", "Flux", "Jenkins", "GitLab CI", "GitHub Actions",
        "CircleCI", "Travis CI", "TeamCity", "Bamboo",
        "Prometheus", "Grafana", "Datadog", "New Relic", "Splunk",
        "PagerDuty", "OpsGenie", "ELK Stack", "Jaeger", "Zipkin",
    ],
    # Cloud Platforms
    "cloud": [
        "AWS", "Amazon Web Services", "Google Cloud Platform", "GCP",
        "Microsoft Azure", "Azure", "DigitalOcean", "Heroku",
        "Oracle Cloud", "IBM Cloud", "Alibaba Cloud",
    ],
    # Programming Languages & Frameworks (backend)
    "languages_frameworks": [
        "Go", "Golang", "Rust", "Scala", "Kotlin", "Elixir",
        "Ruby on Rails", "Django", "Flask", "FastAPI",
        "Spring Boot", "Spring Framework", "Micronaut", "Quarkus",
        "Node.js", "Express.js", "NestJS", "Deno",
        ".NET Core", "ASP.NET", "gRPC", "GraphQL",
    ],
    # Security
    "security": [
        "Okta", "Auth0", "CrowdStrike", "Palo Alto", "Fortinet",
        "Snyk", "SonarQube", "Veracode", "Checkmarx", "HashiCorp Vault",
        "CyberArk", "Duo Security", "Ping Identity", "OneLogin",
    ],
    # ML/AI
    "ml_ai": [
        "TensorFlow", "PyTorch", "MLflow", "Kubeflow", "SageMaker",
        "Vertex AI", "Hugging Face", "scikit-learn", "XGBoost",
        "LightGBM", "Ray", "Weights & Biases", "Neptune.ai",
    ],
    # Communication & Collaboration
    "collaboration": [
        "Slack", "Microsoft Teams", "Jira", "Confluence", "Notion",
        "Asana", "Linear", "Monday.com", "Figma",
    ],
    # CRM & Sales
    "crm_sales": [
        "Salesforce", "HubSpot CRM", "Pipedrive", "Outreach",
        "Gong", "Clari", "ZoomInfo", "Apollo.io",
    ],
}

# Flatten for lookup
ALL_TECHNOLOGIES = set()
TECH_TO_CATEGORY = {}
for category, techs in BACKEND_TECHNOLOGY_TAXONOMY.items():
    for tech in techs:
        ALL_TECHNOLOGIES.add(tech.lower())
        TECH_TO_CATEGORY[tech.lower()] = category
6.2 NLP Entity Recognizer
Python

# processor/src/nlp/entity_recognizer.py
import re
import spacy
import structlog
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from .technology_taxonomy import (
    BACKEND_TECHNOLOGY_TAXONOMY,
    ALL_TECHNOLOGIES,
    TECH_TO_CATEGORY,
)

logger = structlog.get_logger()

@dataclass
class NLPTechnologyDetection:
    technology_identifier: str
    category: str
    detection_vector: str
    confidence: float
    evidence: str
    job_title: str

class JobPostingNLPDetector:
    """
    Layer 4: Extract backend/infrastructure technologies from job postings
    using NLP (Named Entity Recognition + pattern matching).
    """

    def __init__(self, spacy_model: str = "en_core_web_lg"):
        logger.info("Loading spaCy model", model=spacy_model)
        self.nlp = spacy.load(spacy_model)

        # Add custom entity ruler for technology names
        self._add_technology_patterns()

        # Compile context patterns that indicate technology usage
        self._requirement_patterns = [
            re.compile(r"experience\s+(?:with|in|using)\s+(.+?)(?:\.|,|;|\n)", re.IGNORECASE),
            re.compile(r"proficien(?:t|cy)\s+(?:in|with)\s+(.+?)(?:\.|,|;|\n)", re.IGNORECASE),
            re.compile(r"(?:strong|solid|deep)\s+knowledge\s+of\s+(.+?)(?:\.|,|;|\n)", re.IGNORECASE),
            re.compile(r"(?:work|working)\s+(?:with|on)\s+(.+?)(?:\.|,|;|\n)", re.IGNORECASE),
            re.compile(r"(?:build|building|develop|developing)\s+(?:with|using|on)\s+(.+?)(?:\.|,|;|\n)", re.IGNORECASE),
            re.compile(r"our\s+(?:stack|tech\s+stack|technology\s+stack)\s+includes?\s+(.+?)(?:\.|;|\n)", re.IGNORECASE),
            re.compile(r"(?:we\s+use|we\s+leverage|we\s+rely\s+on)\s+(.+?)(?:\.|,|;|\n)", re.IGNORECASE),
            re.compile(r"(?:required|requirements?|qualifications?).*?:\s*(.+?)(?:\n\n|\Z)", re.IGNORECASE | re.DOTALL),
        ]

        # Technology name variations and aliases
        self._aliases = {
            "postgres": "PostgreSQL",
            "pg": "PostgreSQL",
            "mongo": "MongoDB",
            "k8s": "Kubernetes",
            "k8": "Kubernetes",
            "kube": "Kubernetes",
            "tf": "Terraform",
            "aws": "AWS",
            "gcp": "Google Cloud Platform",
            "azure": "Microsoft Azure",
            "react.js": "React",
            "reactjs": "React",
            "node": "Node.js",
            "nodejs": "Node.js",
            "rails": "Ruby on Rails",
            "ror": "Ruby on Rails",
            "es": "Elasticsearch",
            "elastic": "Elasticsearch",
            "redis": "Redis",
            "rabbit": "RabbitMQ",
            "rabbitmq": "RabbitMQ",
        }

        logger.info("NLP detector initialized")

    def _add_technology_patterns(self):
        """Add technology entity patterns to spaCy pipeline."""
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        patterns = []

        for category, techs in BACKEND_TECHNOLOGY_TAXONOMY.items():
            for tech in techs:
                # Add exact match patterns
                patterns.append({
                    "label": "TECHNOLOGY",
                    "pattern": tech
                })
                # Add case-insensitive variations
                patterns.append({
                    "label": "TECHNOLOGY",
                    "pattern": [{"LOWER": w.lower()} for w in tech.split()]
                })

        ruler.add_patterns(patterns)

    def detect(
        self, text: str, domain: str, page_url: str, job_title: str = ""
    ) -> List[NLPTechnologyDetection]:
        """
        Extract technology mentions from job posting text.

        Performs three passes:
        1. SpaCy NER with custom technology entities
        2. Direct taxonomy matching against cleaned text
        3. Context-aware pattern matching for requirement phrases
        """
        detections: List[NLPTechnologyDetection] = []
        seen_technologies: Set[str] = set()

        # Clean the text
        cleaned = self._clean_text(text)

        # Pass 1: SpaCy NER
        doc = self.nlp(cleaned[:50000])  # Limit for performance
        for ent in doc.ents:
            if ent.label_ == "TECHNOLOGY":
                tech_name = self._normalize_technology_name(ent.text)
                if tech_name and tech_name.lower() not in seen_technologies:
                    seen_technologies.add(tech_name.lower())
                    context = self._extract_context(cleaned, ent.start_char, ent.end_char)
                    detections.append(NLPTechnologyDetection(
                        technology_identifier=tech_name,
                        category=TECH_TO_CATEGORY.get(tech_name.lower(), "Unknown"),
                        detection_vector="JOB_POSTING_NLP_NER",
                        confidence=self._calculate_confidence(context, tech_name),
                        evidence=f"NER entity in context: '{context}'",
                        job_title=job_title,
                    ))

        # Pass 2: Direct taxonomy matching
        for tech_lower in ALL_TECHNOLOGIES:
            if tech_lower in seen_technologies:
                continue

            # Use word boundary matching to avoid false positives
            pattern = re.compile(r'\b' + re.escape(tech_lower) + r'\b', re.IGNORECASE)
            match = pattern.search(cleaned)
            if match:
                tech_name = self._normalize_technology_name(match.group())
                if tech_name:
                    seen_technologies.add(tech_name.lower())
                    context = self._extract_context(cleaned, match.start(), match.end())
                    detections.append(NLPTechnologyDetection(
                        technology_identifier=tech_name,
                        category=TECH_TO_CATEGORY.get(tech_name.lower(), "Unknown"),
                        detection_vector="JOB_POSTING_NLP_TAXONOMY",
                        confidence=self._calculate_confidence(context, tech_name),
                        evidence=f"Taxonomy match: '{context}'",
                        job_title=job_title,
                    ))

        # Pass 3: Alias matching
        for alias, canonical in self._aliases.items():
            if canonical.lower() in seen_technologies:
                continue
            pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
            match = pattern.search(cleaned)
            if match:
                seen_technologies.add(canonical.lower())
                context = self._extract_context(cleaned, match.start(), match.end())
                detections.append(NLPTechnologyDetection(
                    technology_identifier=canonical,
                    category=TECH_TO_CATEGORY.get(canonical.lower(), "Unknown"),
                    detection_vector="JOB_POSTING_NLP_ALIAS",
                    confidence=self._calculate_confidence(context, canonical) * 0.9,
                    evidence=f"Alias '{alias}' → {canonical}: '{context}'",
                    job_title=job_title,
                ))

        logger.info(
            "NLP detection complete",
            domain=domain,
            technologies_found=len(detections),
            job_title=job_title,
        )
        return detections

    def _clean_text(self, text: str) -> str:
        """Remove HTML artifacts and normalize whitespace."""
        # Remove HTML tags if any remain
        text = re.sub(r'<[^>]+>', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        return text.strip()

    def _normalize_technology_name(self, raw: str) -> str:
        """Normalize detected technology name to canonical form."""
        lower = raw.strip().lower()

        # Check aliases first
        if lower in self._aliases:
            return self._aliases[lower]

        # Find canonical casing from taxonomy
        for category, techs in BACKEND_TECHNOLOGY_TAXONOMY.items():
            for tech in techs:
                if tech.lower() == lower:
                    return tech

        # Return the original with title casing if not found
        return raw.strip()

    def _extract_context(self, text: str, start: int, end: int, window: int = 80) -> str:
        """Extract surrounding context for evidence."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end].strip()

    def _calculate_confidence(self, context: str, tech_name: str) -> float:
        """
        Calculate confidence score based on contextual signals.
        Higher confidence when technology appears in requirement/skill context.
        """
        base_confidence = 0.70
        context_lower = context.lower()

        # Boost for requirement-oriented language
        requirement_signals = [
            "experience with", "experience in", "proficient",
            "knowledge of", "working with", "expertise in",
            "required", "must have", "strong background",
            "we use", "our stack", "tech stack",
            "hands-on", "build with", "develop using",
        ]
        for signal in requirement_signals:
            if signal in context_lower:
                base_confidence += 0.08
                break

        # Boost for bullet-point list context (typical for requirements)
        if re.search(r'[•\-\*]\s', context):
            base_confidence += 0.05

        # Penalize if in "nice to have" or "bonus" context
        optional_signals = ["nice to have", "bonus", "preferred", "plus"]
        for signal in optional_signals:
            if signal in context_lower:
                base_confidence -= 0.10
                break

        return min(0.98, max(0.50, base_confidence))
6.3 Job Posting Consumer
Python

# processor/src/consumers/job_posting_consumer.py
import orjson
import structlog
from confluent_kafka import Consumer
from bs4 import BeautifulSoup
from typing import List
from ..config import ProcessorConfig
from ..nlp.entity_recognizer import JobPostingNLPDetector
from ..persistence.repository import TechnographicRepository

logger = structlog.get_logger()

class JobPostingConsumer:
    """Consumes job posting HTML and runs Layer 4 NLP detection."""

    def __init__(self, config: ProcessorConfig, repository: TechnographicRepository):
        self.config = config
        self.repository = repository
        self.nlp_detector = JobPostingNLPDetector(config.spacy_model)

        self.consumer = Consumer({
            "bootstrap.servers": config.kafka_brokers,
            "group.id": config.kafka_consumer_group_nlp,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": "600000",  # NLP is slow, allow 10min
        })
        self.consumer.subscribe([config.kafka_topic_jobs])

    def run(self):
        logger.info("Job posting NLP consumer started")

        try:
            while True:
                msg = self.consumer.poll(timeout=2.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.error("Consumer error", error=str(msg.error()))
                    continue

                payload = orjson.loads(msg.value())
                self._process_single(payload)
                self.consumer.commit(asynchronous=True)

        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

    def _process_single(self, payload: dict):
        domain = payload.get("canonical_domain", "")
        url = payload.get("url", "")
        html_body = payload.get("html_body", "")
        timestamp = payload.get("crawl_timestamp")

        if not html_body:
            return

        # Extract text from HTML
        soup = BeautifulSoup(html_body, "lxml")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        text = soup.get_text(separator=" ", strip=True)

        if len(text) < 100:
            logger.debug("Job posting text too short, skipping", domain=domain)
            return

        # Try to extract job title from page
        job_title = self._extract_job_title(soup)

        # Run NLP detection
        detections = self.nlp_detector.detect(text, domain, url, job_title)

        # Persist detections
        all_records = []
        for d in detections:
            all_records.append({
                "canonical_domain": domain,
                "technology_identifier": d.technology_identifier,
                "detection_vector": d.detection_vector,
                "confidence": d.confidence,
                "crawl_timestamp": timestamp,
            })

        if all_records:
            self.repository.batch_upsert_technologies(all_records)
            logger.info(
                "Job posting NLP processed",
                domain=domain,
                url=url,
                technologies_found=len(all_records),
                technologies=[d.technology_identifier for d in detections],
            )

    def _extract_job_title(self, soup: BeautifulSoup) -> str:
        """Attempt to extract job title from page."""
        # Try common patterns
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        title = soup.find("title")
        if title:
            return title.get_text(strip=True)

        return "Unknown"
7. Phase 5: PostgreSQL Data Layer
7.1 Migration Scripts
SQL

-- database/migrations/001_create_scanned_companies.sql
CREATE TABLE IF NOT EXISTS scanned_companies (
    canonical_domain VARCHAR(255) PRIMARY KEY,
    corporate_name VARCHAR(255),
    last_successful_crawl TIMESTAMP WITH TIME ZONE,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_technologies_detected INTEGER DEFAULT 0,
    crawl_count INTEGER DEFAULT 0,
    last_http_status INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for freshness queries
CREATE INDEX idx_companies_last_crawl
    ON scanned_companies(last_successful_crawl);

-- Index for companies needing re-crawl (stale data)
CREATE INDEX idx_companies_stale
    ON scanned_companies(last_successful_crawl)
    WHERE last_successful_crawl < NOW() - INTERVAL '7 days';
SQL

-- database/migrations/002_create_technology_installations.sql
CREATE TABLE IF NOT EXISTS technology_installations (
    id BIGSERIAL,
    canonical_domain VARCHAR(255) NOT NULL
        REFERENCES scanned_companies(canonical_domain)
        ON DELETE CASCADE,
    technology_identifier VARCHAR(100) NOT NULL,
    detection_vector VARCHAR(50) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.00,
    initial_detection_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    latest_verification_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    detection_count INTEGER DEFAULT 1,
    evidence_sample TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Composite unique constraint for upserts
    CONSTRAINT uq_domain_tech_vector
        UNIQUE (canonical_domain, technology_identifier, detection_vector)
);

-- Partition by time for time-series optimization (optional TimescaleDB)
-- SELECT create_hypertable('technology_installations', 'initial_detection_date',
--     chunk_time_interval => INTERVAL '1 month',
--     if_not_exists => TRUE
-- );
SQL

-- database/migrations/003_create_indexes.sql

-- Primary query patterns: "What technologies does company X use?"
CREATE INDEX idx_tech_by_domain
    ON technology_installations(canonical_domain);

-- "Which companies use technology Y?"
CREATE INDEX idx_tech_by_technology
    ON technology_installations(technology_identifier);

-- "Show me all technologies detected via NLP"
CREATE INDEX idx_tech_by_vector
    ON technology_installations(detection_vector);

-- Time-series: "Technology adoption over last 90 days"
CREATE INDEX idx_tech_by_detection_date
    ON technology_installations(initial_detection_date DESC);

-- Active technologies only
CREATE INDEX idx_tech_active
    ON technology_installations(canonical_domain, technology_identifier)
    WHERE is_active = TRUE;

-- Composite for dashboard queries
CREATE INDEX idx_tech_domain_date
    ON technology_installations(canonical_domain, latest_verification_date DESC);

-- Full-text search on technology names (for API queries)
CREATE INDEX idx_tech_name_trgm
    ON technology_installations
    USING gin (technology_identifier gin_trgm_ops);

-- Requires: CREATE EXTENSION IF NOT EXISTS pg_trgm;
SQL

-- database/migrations/004_create_views.sql

-- Materialized view for technology adoption summary
CREATE MATERIALIZED VIEW technology_adoption_summary AS
SELECT
    technology_identifier,
    detection_vector,
    COUNT(DISTINCT canonical_domain) AS company_count,
    MIN(initial_detection_date) AS earliest_adoption,
    MAX(latest_verification_date) AS latest_verification,
    AVG(confidence) AS avg_confidence
FROM technology_installations
WHERE is_active = TRUE
GROUP BY technology_identifier, detection_vector
ORDER BY company_count DESC;

CREATE UNIQUE INDEX idx_adoption_summary_tech
    ON technology_adoption_summary(technology_identifier, detection_vector);

-- Refresh periodically
-- REFRESH MATERIALIZED VIEW CONCURRENTLY technology_adoption_summary;

-- View for stale companies needing re-crawl
CREATE VIEW companies_needing_recrawl AS
SELECT
    canonical_domain,
    corporate_name,
    last_successful_crawl,
    NOW() - last_successful_crawl AS staleness
FROM scanned_companies
WHERE last_successful_crawl < NOW() - INTERVAL '7 days'
   OR last_successful_crawl IS NULL
ORDER BY last_successful_crawl ASC NULLS FIRST;
7.2 SQLAlchemy Models
Python

# processor/src/persistence/models.py
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Numeric,
    Text, ForeignKey, UniqueConstraint, Index, BigInteger
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from datetime import datetime

class Base(DeclarativeBase):
    pass

class ScannedCompany(Base):
    __tablename__ = "scanned_companies"

    canonical_domain = Column(String(255), primary_key=True)
    corporate_name = Column(String(255), nullable=True)
    last_successful_crawl = Column(DateTime(timezone=True))
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    total_technologies_detected = Column(Integer, default=0)
    crawl_count = Column(Integer, default=0)
    last_http_status = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    technologies = relationship(
        "TechnologyInstallation",
        back_populates="company",
        cascade="all, delete-orphan"
    )

class TechnologyInstallation(Base):
    __tablename__ = "technology_installations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    canonical_domain = Column(
        String(255),
        ForeignKey("scanned_companies.canonical_domain", ondelete="CASCADE"),
        nullable=False,
    )
    technology_identifier = Column(String(100), nullable=False)
    detection_vector = Column(String(50), nullable=False)
    confidence = Column(Numeric(3, 2), default=0.00)
    initial_detection_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    latest_verification_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_active = Column(Boolean, default=True)
    detection_count = Column(Integer, default=1)
    evidence_sample = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("ScannedCompany", back_populates="technologies")

    __table_args__ = (
        UniqueConstraint(
            "canonical_domain", "technology_identifier", "detection_vector",
            name="uq_domain_tech_vector"
        ),
    )
7.3 Repository Layer
Python

# processor/src/persistence/repository.py
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Dict, Optional
from datetime import datetime, timezone
from .models import Base, ScannedCompany, TechnologyInstallation
from ..config import ProcessorConfig

logger = structlog.get_logger()

class TechnographicRepository:
    """Data access layer for technographic data persistence."""

    def __init__(self, config: ProcessorConfig):
        self.engine = create_engine(
            config.database_url,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False,
        )
        self.SessionFactory = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        logger.info("Database repository initialized", url=config.db_host)

    def upsert_company(
        self,
        domain: str,
        crawl_timestamp: str,
        corporate_name: Optional[str] = None,
        http_status: Optional[int] = None,
    ):
        """Upsert a company record with latest crawl info."""
        stmt = pg_insert(ScannedCompany).values(
            canonical_domain=domain,
            corporate_name=corporate_name,
            last_successful_crawl=crawl_timestamp,
            crawl_count=1,
            last_http_status=http_status,
        ).on_conflict_do_update(
            index_elements=["canonical_domain"],
            set_={
                "last_successful_crawl": crawl_timestamp,
                "crawl_count": ScannedCompany.crawl_count + 1,
                "last_http_status": http_status,
                "updated_at": datetime.now(timezone.utc),
                # Only update corporate_name if we have a new value
                **({"corporate_name": corporate_name} if corporate_name else {}),
            }
        )

        with self.SessionFactory() as session:
            session.execute(stmt)
            session.commit()

    def batch_upsert_technologies(self, detections: List[Dict]):
        """
        Batch upsert technology detections with proper time-series semantics:
        - If new: insert with initial_detection_date = now
        - If existing: update latest_verification_date and increment count
        """
        if not detections:
            return

        with self.SessionFactory() as session:
            for detection in detections:
                stmt = pg_insert(TechnologyInstallation).values(
                    canonical_domain=detection["canonical_domain"],
                    technology_identifier=detection["technology_identifier"],
                    detection_vector=detection["detection_vector"],
                    confidence=detection.get("confidence", 0.80),
                    initial_detection_date=detection.get("crawl_timestamp", datetime.now(timezone.utc)),
                    latest_verification_date=detection.get("crawl_timestamp", datetime.now(timezone.utc)),
                    is_active=True,
                    detection_count=1,
                ).on_conflict_do_update(
                    constraint="uq_domain_tech_vector",
                    set_={
                        "latest_verification_date": detection.get(
                            "crawl_timestamp", datetime.now(timezone.utc)
                        ),
                        "is_active": True,
                        "detection_count": TechnologyInstallation.detection_count + 1,
                        "confidence": detection.get("confidence", 0.80),
                    }
                )
                session.execute(stmt)

            session.commit()
            logger.debug("Technologies upserted", count=len(detections))

    def get_company_technologies(self, domain: str) -> List[Dict]:
        """Get all active technologies for a company."""
        with self.SessionFactory() as session:
            results = session.query(TechnologyInstallation).filter(
                TechnologyInstallation.canonical_domain == domain,
                TechnologyInstallation.is_active == True,
            ).order_by(
                TechnologyInstallation.confidence.desc()
            ).all()

            return [
                {
                    "technology": r.technology_identifier,
                    "vector": r.detection_vector,
                    "confidence": float(r.confidence) if r.confidence else 0,
                    "first_seen": r.initial_detection_date.isoformat() if r.initial_detection_date else None,
                    "last_verified": r.latest_verification_date.isoformat() if r.latest_verification_date else None,
                    "detection_count": r.detection_count,
                }
                for r in results
            ]

    def find_companies_by_technology(
        self, technology: str, limit: int = 100
    ) -> List[Dict]:
        """Find all companies using a specific technology."""
        with self.SessionFactory() as session:
            results = session.query(TechnologyInstallation).filter(
                TechnologyInstallation.technology_identifier.ilike(f"%{technology}%"),
                TechnologyInstallation.is_active == True,
            ).limit(limit).all()

            return [
                {
                    "domain": r.canonical_domain,
                    "technology": r.technology_identifier,
                    "vector": r.detection_vector,
                    "confidence": float(r.confidence) if r.confidence else 0,
                    "first_seen": r.initial_detection_date.isoformat() if r.initial_detection_date else None,
                }
                for r in results
            ]

    def mark_stale_technologies(self, staleness_days: int = 30):
        """Mark technologies as inactive if not verified recently."""
        with self.SessionFactory() as session:
            session.execute(
                text("""
                    UPDATE technology_installations
                    SET is_active = FALSE
                    WHERE latest_verification_date < NOW() - INTERVAL ':days days'
                    AND is_active = TRUE
                """),
                {"days": staleness_days}
            )
            session.commit()
            logger.info("Stale technologies marked inactive", staleness_days=staleness_days)
7.4 Main Processor Entrypoint
Python

# processor/src/main.py
import sys
import multiprocessing
import structlog
from .config import ProcessorConfig
from .persistence.repository import TechnographicRepository
from .consumers.html_consumer import HTMLPayloadConsumer
from .consumers.dns_consumer import DNSPayloadConsumer
from .consumers.job_posting_consumer import JobPostingConsumer

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer() if sys.stdout.isatty() else structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()

def run_html_consumer(config_dict: dict):
    config = ProcessorConfig(**config_dict)
    repo = TechnographicRepository(config)
    consumer = HTMLPayloadConsumer(config, repo)
    consumer.run()

def run_dns_consumer(config_dict: dict):
    config = ProcessorConfig(**config_dict)
    repo = TechnographicRepository(config)
    consumer = DNSPayloadConsumer(config, repo)
    consumer.run()

def run_nlp_consumer(config_dict: dict):
    config = ProcessorConfig(**config_dict)
    repo = TechnographicRepository(config)
    consumer = JobPostingConsumer(config, repo)
    consumer.run()

def main():
    config = ProcessorConfig()
    config_dict = config.model_dump()

    logger.info("Starting technographic processor pipeline")

    processes = [
        multiprocessing.Process(
            target=run_html_consumer, args=(config_dict,), name="html-consumer"
        ),
        multiprocessing.Process(
            target=run_dns_consumer, args=(config_dict,), name="dns-consumer"
        ),
        multiprocessing.Process(
            target=run_nlp_consumer, args=(config_dict,), name="nlp-consumer"
        ),
    ]

    for p in processes:
        p.start()
        logger.info("Started consumer process", name=p.name, pid=p.pid)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.info("Shutting down all consumers")
        for p in processes:
            p.terminate()
            p.join(timeout=10)

if __name__ == "__main__":
    main()
8. Phase 6: Orchestration, Deployment & Monitoring
8.1 Crawler Dockerfile
Dockerfile

# crawler/Dockerfile
FROM rust:1.75-bookworm AS builder

WORKDIR /app
# Cache dependencies
COPY crawler/Cargo.toml crawler/Cargo.lock ./
COPY crawler/crates/ ./crates/

# Build with release optimizations
RUN cargo build --release --bin crawler-core

# Runtime image
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/crawler-core /usr/local/bin/crawler

# Non-root user
RUN useradd -m -s /bin/bash crawler
USER crawler

ENTRYPOINT ["crawler"]
8.2 Processor Dockerfile
Dockerfile

# processor/Dockerfile
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_lg

COPY processor/src/ ./src/

RUN useradd -m -s /bin/bash processor
USER processor

CMD ["python", "-m", "src.main"]
8.3 Kubernetes Deployments
YAML

# infra/kubernetes/crawler-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: technographic-crawler
  namespace: technographics
  labels:
    app: crawler
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crawler
  template:
    metadata:
      labels:
        app: crawler
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      containers:
      - name: crawler
        image: technographic-engine/crawler:latest
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
        env:
        - name: KAFKA_BROKERS
          value: "redpanda.technographics.svc.cluster.local:9092"
        - name: MAX_CONCURRENT_CONNECTIONS
          value: "2000"
        - name: GLOBAL_MAX_RPS
          value: "1500"
        - name: RUST_LOG
          value: "crawler_core=info"
        volumeMounts:
        - name: domains
          mountPath: /data/domains
      volumes:
      - name: domains
        configMap:
          name: seed-domains
YAML

# infra/kubernetes/processor-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: technographic-processor
  namespace: technographics
spec:
  replicas: 5
  selector:
    matchLabels:
      app: processor
  template:
    metadata:
      labels:
        app: processor
    spec:
      containers:
      - name: processor
        image: technographic-engine/processor:latest
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
        env:
        - name: TECHNO_KAFKA_BROKERS
          value: "redpanda.technographics.svc.cluster.local:9092"
        - name: TECHNO_DB_HOST
          value: "postgres.technographics.svc.cluster.local"
        - name: TECHNO_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
8.4 Prometheus Metrics
Python

# processor/src/utils/metrics.py
from prometheus_client import (
    Counter, Histogram, Gauge, start_http_server, Info
)

# Counters
MESSAGES_CONSUMED = Counter(
    'technographic_messages_consumed_total',
    'Total messages consumed from Kafka',
    ['topic', 'consumer_group']
)

TECHNOLOGIES_DETECTED = Counter(
    'technographic_technologies_detected_total',
    'Total technology detections',
    ['detection_vector']
)

DB_WRITES = Counter(
    'technographic_db_writes_total',
    'Total database write operations',
    ['operation']
)

CONSUMER_ERRORS = Counter(
    'technographic_consumer_errors_total',
    'Total consumer processing errors',
    ['consumer', 'error_type']
)

# Histograms
PROCESSING_DURATION = Histogram(
    'technographic_processing_duration_seconds',
    'Time to process a single message',
    ['detector_layer'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

NLP_INFERENCE_DURATION = Histogram(
    'technographic_nlp_inference_seconds',
    'Time for NLP inference on a job posting',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Gauges
CONSUMER_LAG = Gauge(
    'technographic_consumer_lag',
    'Consumer group lag in messages',
    ['consumer_group', 'topic', 'partition']
)

COMPANIES_SCANNED = Gauge(
    'technographic_companies_scanned_total',
    'Total unique companies in database'
)

def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics HTTP server."""
    start_http_server(port)
8.5 Grafana Dashboard (JSON Model)
JSON

// infra/kubernetes/monitoring/grafana-dashboards.json
{
  "dashboard": {
    "title": "Technographic Discovery Engine",
    "panels": [
      {
        "title": "Messages Consumed / min",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(technographic_messages_consumed_total[1m])",
            "legendFormat": "{{topic}}"
          }
        ]
      },
      {
        "title": "Technologies Detected / min",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(technographic_technologies_detected_total[1m])",
            "legendFormat": "{{detection_vector}}"
          }
        ]
      },
      {
        "title": "Processing Latency (p95)",
        "type": "gauge",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(technographic_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "{{detector_layer}}"
          }
        ]
      },
      {
        "title": "Consumer Lag",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(technographic_consumer_lag) by (consumer_group)",
            "legendFormat": "{{consumer_group}}"
          }
        ]
      },
      {
        "title": "NLP Inference Latency (p99)",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(technographic_nlp_inference_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Total Companies Scanned",
        "type": "stat",
        "targets": [
          {
            "expr": "technographic_companies_scanned_total"
          }
        ]
      }
    ]
  }
}
9. Phase 7: Testing, Benchmarking & Hardening
9.1 Rust Integration Tests
Rust

// crawler/tests/integration_tests.rs
use crawler_core::fetcher::Fetcher;
use crawler_core::config::CrawlerConfig;
use crawler_core::rate_limiter::DistributedRateLimiter;
use crawler_core::robots::RobotsCache;
use crawler_core::dns_resolver::DnsResolver;
use std::sync::Arc;
use std::time::Duration;

#[tokio::test]
async fn test_fetcher_basic_request() {
    let config = Arc::new(CrawlerConfig::default());
    let rate_limiter = Arc::new(DistributedRateLimiter::new(100, 5));
    let client = reqwest::Client::new();
    let robots_cache = Arc::new(RobotsCache::new(Duration::from_secs(300), client));

    let fetcher = Fetcher::new(config, rate_limiter, robots_cache).unwrap();
    let result = fetcher.fetch("example.com", "https://example.com").await;

    assert!(result.is_ok());
    let payload = result.unwrap();
    assert_eq!(payload.http_status, 200);
    assert!(payload.html_body.is_some());
}

#[tokio::test]
async fn test_rate_limiter_enforces_limits() {
    let limiter = DistributedRateLimiter::new(10, 2);
    let start = std::time::Instant::now();

    for _ in 0..5 {
        limiter.acquire("test.com").await;
    }

    let elapsed = start.elapsed();
    // 5 requests at 2 RPS for test.com should take at least ~2 seconds
    assert!(elapsed.as_secs() >= 2, "Rate limiter not enforcing domain limits");
}

#[tokio::test]
async fn test_dns_resolver() {
    let resolver = DnsResolver::new().await.unwrap();
    let result = resolver.resolve_all("google.com").await;

    assert!(result.is_ok());
    let dns = result.unwrap();
    assert!(!dns.a_records.is_empty());
    assert!(!dns.mx_records.is_empty());
}

#[tokio::test]
async fn test_robots_txt_compliance() {
    let client = reqwest::Client::new();
    let cache = RobotsCache::new(Duration::from_secs(300), client);

    // Google typically disallows /search
    let allowed = cache.is_allowed("google.com", "/", "TestBot").await;
    assert!(allowed);
}
9.2 Python Unit Tests
Python

# processor/tests/test_html_detector.py
import pytest
from src.detectors.html_detector import HTMLTechnographicDetector

@pytest.fixture
def detector():
    return HTMLTechnographicDetector()

class TestHTMLDetector:

    def test_detect_google_analytics(self, detector):
        html = '''
        <html>
        <head>
            <script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123"></script>
            <script>
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', 'G-ABC123');
            </script>
        </head>
        <body>Hello World</body>
        </html>
        '''
        detections = detector.detect(html, "https://example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "Google Analytics" in tech_names or "Google Tag Manager" in tech_names

    def test_detect_hubspot(self, detector):
        html = '''
        <html>
        <head></head>
        <body>
            <script type="text/javascript" id="hs-script-loader" async defer
                src="//js.hs-scripts.com/12345.js"></script>
        </body>
        </html>
        '''
        detections = detector.detect(html, "https://example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "HubSpot" in tech_names

    def test_detect_wordpress(self, detector):
        html = '''
        <html>
        <head>
            <meta name="generator" content="WordPress 6.4.2" />
            <link rel="stylesheet" href="/wp-content/themes/theme/style.css" />
        </head>
        <body></body>
        </html>
        '''
        detections = detector.detect(html, "https://example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "WordPress" in tech_names

    def test_detect_react(self, detector):
        html = '<html><body><div id="root" data-reactroot=""></div></body></html>'
        detections = detector.detect(html, "https://example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "React" in tech_names

    def test_no_false_positives_on_empty_html(self, detector):
        html = "<html><body>Simple page with no technologies</body></html>"
        detections = detector.detect(html, "https://example.com")
        assert len(detections) == 0

    def test_detect_multiple_technologies(self, detector):
        html = '''
        <html>
        <head>
            <script async src="https://www.googletagmanager.com/gtag/js"></script>
        </head>
        <body>
            <div data-reactroot="">
                <script src="https://js.stripe.com/v3/"></script>
                <script src="https://widget.intercom.io/widget/abc123"></script>
            </div>
        </body>
        </html>
        '''
        detections = detector.detect(html, "https://example.com")
        assert len(detections) >= 3
Python

# processor/tests/test_header_detector.py
import pytest
from src.detectors.header_detector import HeaderTechnographicDetector

@pytest.fixture
def detector():
    return HeaderTechnographicDetector()

class TestHeaderDetector:

    def test_detect_cloudflare(self, detector):
        headers = {
            "server": "cloudflare",
            "cf-ray": "abc123-SJC",
            "content-type": "text/html",
        }
        detections = detector.detect(headers, "example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "Cloudflare" in tech_names

    def test_detect_nginx(self, detector):
        headers = {"server": "nginx/1.24.0", "content-type": "text/html"}
        detections = detector.detect(headers, "example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "Nginx" in tech_names

    def test_detect_vercel(self, detector):
        headers = {"x-vercel-id": "sfo1::abc123", "server": "Vercel"}
        detections = detector.detect(headers, "example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "Vercel" in tech_names

    def test_detect_php_from_cookie(self, detector):
        headers = {"set-cookie": "PHPSESSID=abc123; path=/"}
        detections = detector.detect(headers, "example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "PHP" in tech_names
Python

# processor/tests/test_dns_detector.py
import pytest
from src.detectors.dns_detector import DNSTechnographicDetector

@pytest.fixture
def detector():
    return DNSTechnographicDetector()

class TestDNSDetector:

    def test_detect_google_workspace(self, detector):
        dns_payload = {
            "mx_records": [
                {"preference": 10, "exchange": "alt1.aspmx.l.google.com."},
                {"preference": 5, "exchange": "aspmx.l.google.com."},
            ],
            "txt_records": [],
            "ns_records": [],
        }
        detections = detector.detect(dns_payload, "example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "Google Workspace" in tech_names

    def test_detect_sendgrid_from_spf(self, detector):
        dns_payload = {
            "mx_records": [],
            "txt_records": [
                "v=spf1 include:sendgrid.net include:_spf.google.com ~all"
            ],
            "ns_records": [],
        }
        detections = detector.detect(dns_payload, "example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "SendGrid" in tech_names

    def test_detect_cloudflare_dns(self, detector):
        dns_payload = {
            "mx_records": [],
            "txt_records": [],
            "ns_records": [
                "ali.ns.cloudflare.com.",
                "bob.ns.cloudflare.com.",
            ],
        }
        detections = detector.detect(dns_payload, "example.com")
        tech_names = [d.technology_identifier for d in detections]
        assert "Cloudflare DNS" in tech_names
Python

# processor/tests/test_nlp_detector.py
import pytest
from src.nlp.entity_recognizer import JobPostingNLPDetector

@pytest.fixture
def detector():
    return JobPostingNLPDetector()

class TestNLPDetector:

    def test_detect_backend_technologies(self, detector):
        text = """
        Senior Data Engineer

        We are looking for a Senior Data Engineer to join our growing
        data platform team. You will be responsible for building and
        maintaining our data infrastructure.

        Requirements:
        • 5+ years of experience with Python and SQL
        • Strong experience with Apache Spark and Apache Airflow
        • Proficiency in Snowflake data warehouse
        • Experience with Kubernetes and Docker
        • Knowledge of Terraform for infrastructure-as-code
        • Familiarity with dbt for data transformation

        Our tech stack includes:
        - Apache Kafka for event streaming
        - PostgreSQL and Redis for operational data
        - Databricks for analytics
        - Datadog for monitoring
        """
        detections = detector.detect(text, "example.com", "https://careers.example.com/jobs/123", "Senior Data Engineer")
        tech_names = [d.technology_identifier for d in detections]

        assert "Apache Spark" in tech_names
        assert "Apache Airflow" in tech_names
        assert "Snowflake" in tech_names
        assert "Kubernetes" in tech_names
        assert "Docker" in tech_names
        assert "Terraform" in tech_names
        assert "Apache Kafka" in tech_names
        assert "PostgreSQL" in tech_names
        assert "Redis" in tech_names

    def test_detect_aliases(self, detector):
        text = """
        We need someone with experience in k8s, mongo, and postgres.
        Must know AWS and have worked with node and rails.
        """
        detections = detector.detect(text, "example.com", "https://example.com/jobs", "")
        tech_names = [d.technology_identifier for d in detections]

        assert "Kubernetes" in tech_names
        assert "MongoDB" in tech_names
        assert "PostgreSQL" in tech_names

    def test_confidence_scoring(self, detector):
        text_high = "Required: 5+ years of hands-on experience with Apache Kafka"
        text_low = "Nice to have: some exposure to Apache Kafka"

        detections_high = detector.detect(text_high, "a.com", "http://a.com/jobs", "")
        detections_low = detector.detect(text_low, "b.com", "http://b.com/jobs", "")

        kafka_high = [d for d in detections_high if d.technology_identifier == "Apache Kafka"]
        kafka_low = [d for d in detections_low if d.technology_identifier == "Apache Kafka"]

        if kafka_high and kafka_low:
            assert kafka_high[0].confidence > kafka_low[0].confidence

    def test_no_false_positives(self, detector):
        text = """
        We are looking for a marketing manager with 3+ years experience
        in B2B marketing. Must have strong communication skills and
        experience managing social media campaigns.
        """
        detections = detector.detect(text, "example.com", "http://example.com/jobs", "Marketing Manager")
        # Should have very few or no backend technology detections
        assert len(detections) <= 2  # might pick up "B2B" or similar false positives
9.3 Benchmark Scripts
Python

# scripts/benchmark_crawler.py
"""
Benchmark script to measure crawler throughput and latency.
"""
import asyncio
import time
import statistics
import subprocess

async def benchmark_dns_resolution():
    """Benchmark DNS resolution throughput."""
    import hickory_resolver
    # This would be run separately as it requires Rust bindings
    pass

def benchmark_html_detection():
    """Benchmark HTML detection throughput."""
    from processor.src.detectors.html_detector import HTMLTechnographicDetector

    detector = HTMLTechnographicDetector()

    # Generate sample HTML payloads
    sample_html = '''
    <html>
    <head>
        <script async src="https://www.googletagmanager.com/gtag/js"></script>
        <meta name="generator" content="WordPress 6.4" />
    </head>
    <body>
        <div data-reactroot="">
            <script src="https://js.stripe.com/v3/"></script>
            <script src="https://widget.intercom.io/widget/abc"></script>
            <script src="https://js.hs-scripts.com/12345.js"></script>
        </div>
    </body>
    </html>
    '''

    iterations = 10000
    start = time.perf_counter()

    for _ in range(iterations):
        detector.detect(sample_html, "https://bench.example.com")

    elapsed = time.perf_counter() - start
    rate = iterations / elapsed

    print(f"HTML Detection Benchmark:")
    print(f"  Iterations: {iterations}")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Rate: {rate:.0f} pages/second")
    print(f"  Avg latency: {(elapsed/iterations)*1000:.2f}ms")

def benchmark_nlp_detection():
    """Benchmark NLP detection throughput."""
    from processor.src.nlp.entity_recognizer import JobPostingNLPDetector

    detector = JobPostingNLPDetector()

    sample_text = """
    Senior Software Engineer - Backend
    Requirements:
    - 5+ years experience with Python, Go, or Java
    - Experience with PostgreSQL, Redis, and Elasticsearch
    - Knowledge of Kubernetes, Docker, and Terraform
    - Familiarity with Apache Kafka and Apache Airflow
    - Experience with AWS services (EC2, S3, Lambda, RDS)
    """

    iterations = 500
    latencies = []

    for _ in range(iterations):
        start = time.perf_counter()
        detector.detect(sample_text, "bench.com", "https://bench.com/jobs", "SWE")
        latencies.append(time.perf_counter() - start)

    print(f"\nNLP Detection Benchmark:")
    print(f"  Iterations: {iterations}")
    print(f"  Avg latency: {statistics.mean(latencies)*1000:.1f}ms")
    print(f"  P50 latency: {statistics.median(latencies)*1000:.1f}ms")
    print(f"  P95 latency: {sorted(latencies)[int(0.95*len(latencies))]*1000:.1f}ms")
    print(f"  P99 latency: {sorted(latencies)[int(0.99*len(latencies))]*1000:.1f}ms")
    print(f"  Rate: {iterations/sum(latencies):.0f} postings/second")

if __name__ == "__main__":
    benchmark_html_detection()
    benchmark_nlp_detection()
9.4 CI/CD Pipeline
YAML

# .github/workflows/rust-ci.yml
name: Rust CI

on:
  push:
    paths: ['crawler/**']
  pull_request:
    paths: ['crawler/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
        components: clippy, rustfmt
    - name: Cache cargo
      uses: actions/cache@v3
      with:
        path: |
          ~/.cargo/registry
          ~/.cargo/git
          crawler/target
        key: ${{ runner.os }}-cargo-${{ hashFiles('crawler/Cargo.lock') }}

    - name: Check formatting
      run: cd crawler && cargo fmt --all -- --check

    - name: Clippy lints
      run: cd crawler && cargo clippy --all-targets -- -D warnings

    - name: Run tests
      run: cd crawler && cargo nextest run

    - name: Security audit
      run: cd crawler && cargo audit

    - name: Build release
      run: cd crawler && cargo build --release
YAML

# .github/workflows/python-ci.yml
name: Python CI

on:
  push:
    paths: ['processor/**']
  pull_request:
    paths: ['processor/**']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: technographics_test
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd processor
        pip install -e ".[dev]"
        python -m spacy download en_core_web_sm  # small model for CI

    - name: Lint
      run: |
        cd processor
        ruff check src/ tests/
        black --check src/ tests/

    - name: Type check
      run: cd processor && mypy src/ --ignore-missing-imports

    - name: Run tests
      env:
        TECHNO_DB_HOST: localhost
        TECHNO_DB_NAME: technographics_test
        TECHNO_DB_USER: testuser
        TECHNO_DB_PASSWORD: testpass
        TECHNO_SPACY_MODEL: en_core_web_sm
      run: cd processor && pytest tests/ -v --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3