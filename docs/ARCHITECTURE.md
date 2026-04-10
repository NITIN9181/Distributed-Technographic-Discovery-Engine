# Architecture

## System Overview

TechDetector is a distributed technographic discovery engine. It identifies the software
technologies used by websites through automated scanning and multi-vector detection.

## Components

### 1. CLI (`techdetector/cli.py`)
- User-facing command-line interface built with Click + Rich
- Supports domain enqueueing, scanning, querying, and database management
- Reads from `domains.txt` or accepts individual domains

### 2. Orchestrator (`techdetector/orchestrator.py`)
- Manages the domain queue in Redis
- Deduplicates domains based on recency (configurable `skip_recent_hours`)
- Provides queue statistics for monitoring

### 3. Rust Crawler (`rust_crawler/src/main.rs`)
- High-throughput async crawler built with Tokio
- Consumes domains from Redis queue (`domains:pending`)
- Performs concurrent: HTTP fetch, career page discovery, DNS resolution, TLS inspection
- Respects robots.txt via a shared cache
- Distributed rate limiting via Redis
- Publishes structured results to Redis Stream (`crawl:results`)
- Exposes Prometheus metrics on `:9090/metrics`

### 4. Python Workers (`techdetector/workers/`)
- Pool of detection processors consuming from Redis Stream
- Four detection vectors:
  - **HTMLDetector** — regex pattern matching on HTML source
  - **HeaderDetector** — pattern matching on HTTP response headers
  - **DNSDetector** — analysis of DNS records (MX, CNAME, TXT, NS)
  - **JobPostingDetector** — spaCy NLP on career page text
- Persists results to PostgreSQL with upsert logic
- Health check endpoint on `:8080/health`
- Prometheus metrics on `:9090/metrics`

### 5. PostgreSQL Database
- `scanned_companies` — canonical domain registry with crawl timestamps
- `technology_installations` — detected technologies with evidence and vector info
- Indexes on detection vector, technology ID, category, and timestamps

### 6. Redis
- **Queue** (`domains:pending`) — FIFO list for domain crawl requests
- **Stream** (`crawl:results`) — ordered log of crawl results for worker consumption
- **Sorted Set** (`domains:crawled`) — recency tracking for deduplication
- **Rate Limit Keys** — per-domain token bucket state

## Data Flow

```
1. User enqueues domains via CLI → Redis list
2. Rust Crawler pops domains, performs concurrent scans
3. Crawler publishes structured JSON to Redis Stream
4. Python Workers consume stream messages in consumer groups
5. Workers run 4 detection vectors on each message
6. Detections are upserted to PostgreSQL
7. Prometheus scrapes metrics from crawler + workers
8. Grafana renders dashboards from Prometheus data
```

## Detection Signatures

Technologies are defined in `techdetector/signatures.json` with patterns for each vector:
- `html_patterns` — regex patterns to match in HTML source
- `header_patterns` — key-value pairs to match in HTTP headers
- `dns_indicators` — DNS record patterns (MX, CNAME, TXT)
- `meta` — technology metadata (name, category, website)

## Scaling

| Component | Scaling Model | Bottleneck |
|-----------|--------------|------------|
| Crawler | Horizontal (replicas) | Network I/O, rate limits |
| Workers | Horizontal (replicas) | CPU (NLP), DB write throughput |
| Redis | Vertical (memory) | Stream length, queue depth |
| PostgreSQL | Vertical (CPU, IOPS) | Write throughput at scale |

## Security Considerations

- All secrets stored in Kubernetes Secrets (never ConfigMaps)
- Database credentials injected via environment variables
- No raw SQL from user input (parameterized queries only)
- Docker images scanned with Trivy in CI
- Python deps audited with pip-audit
