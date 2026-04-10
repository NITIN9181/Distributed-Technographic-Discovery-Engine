# CLI & API Reference

## CLI Commands

TechDetector provides a Click-based CLI accessible via `python -m techdetector`.

### `init-db`

Initialize the PostgreSQL database schema.

```bash
python -m techdetector init-db
```

### `scan`

Scan a single domain with specified detection vectors.

```bash
python -m techdetector scan <url> [--vectors html,headers,dns,job_posting]

# Examples
python -m techdetector scan example.com
python -m techdetector scan https://stripe.com --vectors html,headers
python -m techdetector scan github.com --vectors dns
```

**Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--vectors` | `html,headers` | Comma-separated list of detection vectors |

### `enqueue`

Enqueue domains from a file for distributed crawling.

```bash
python -m techdetector enqueue <file> [--force] [--skip-recent-hours 24]

# Examples
python -m techdetector enqueue domains.txt
python -m techdetector enqueue domains.txt --force
```

**Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--force` | `false` | Bypass recency check |
| `--skip-recent-hours` | `24` | Skip domains crawled within N hours |

### `status`

Show current pipeline status and queue statistics.

```bash
python -m techdetector status
```

**Output:**
```
Pipeline Status:
  Domains Pending:      142
  Messages in Stream:   23
  Messages Pending Ack: 5
  Total Crawled:        1,847
```

### `query`

Query detected technologies from the database.

```bash
python -m techdetector query --tech <technology_id>
python -m techdetector query --vector <vector_name>
python -m techdetector query --domain <domain>

# Examples
python -m techdetector query --tech google_analytics
python -m techdetector query --vector DNS_RECORD
python -m techdetector query --domain stripe.com
```

### `export`

Export detection results to CSV.

```bash
python -m techdetector export [--output results.csv] [--tech <id>] [--vector <vector>]
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://techdetector:localdev123@localhost:5432/techdetector` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `MAX_CONCURRENT` | `500` | Max concurrent crawler connections |
| `WORKER_BATCH_SIZE` | `10` | Messages per worker batch |
| `METRICS_PORT` | `9090` | Prometheus metrics port |
| `WORKER_HEALTH_PORT` | `8080` | Worker health check port |
| `RESPECT_ROBOTS` | `true` | Honor robots.txt |
| `SKIP_RECENT_HOURS` | `24` | Skip recently crawled domains |
| `RUST_LOG` | `info` | Rust log level |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy model for NLP |

## Prometheus Metrics

### Python Worker Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `techdetector_detections_total` | Counter | `vector`, `technology`, `category` | Technologies detected |
| `techdetector_detection_duration_seconds` | Histogram | `vector` | Detection pipeline duration |
| `techdetector_messages_processed_total` | Counter | `status` | Messages processed (success/error) |
| `techdetector_message_processing_seconds` | Histogram | — | Per-message processing time |
| `techdetector_queue_depth` | Gauge | `queue` | Queue depth (pending/stream) |
| `techdetector_db_operations_total` | Counter | `operation`, `status` | DB operation counts |

### Rust Crawler Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `crawler_requests_total` | Counter | HTTP requests made |
| `crawler_request_duration_seconds` | Histogram | Request duration |
| `crawler_active_connections` | Gauge | Active HTTP connections |
| `crawler_dns_lookups_total` | Counter | DNS lookups performed |
| `crawler_messages_published_total` | Counter | Messages published to stream |
| `crawler_publish_errors_total` | Counter | Failed publishes |
| `crawler_domains_skipped_total` | Counter | Domains skipped (robots.txt) |

## Health Endpoints

| Service | Endpoint | Method | Response |
|---------|----------|--------|----------|
| Crawler | `/health` | GET | `200 OK` |
| Crawler | `/metrics` | GET | Prometheus text format |
| Worker | `/health` | GET | `{"status": "healthy", "processed_count": N}` |
| Worker | `/metrics` | GET | Prometheus text format |
