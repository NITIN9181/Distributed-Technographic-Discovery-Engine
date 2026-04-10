# TechDetector

Distributed Technographic Discovery Engine for detecting software stacks
used by millions of companies.

## Overview

TechDetector is a high-throughput distributed system that scans websites to identify
the technologies they use. It detects analytics tools, CDNs, frameworks, CMS platforms,
payment processors, and more through four detection vectors:

- **HTML Source Analysis** — Pattern matching against script tags, meta tags, and DOM structure
- **HTTP Header Detection** — Identifying technologies from server headers and response metadata
- **DNS Record Analysis** — Detecting CDNs, email providers, and hosting from DNS records
- **Job Posting NLP** — Natural language processing on career pages to infer tech stacks

## Architecture

```
┌─────────┐     ┌───────────┐     ┌───────────────┐     ┌──────────┐
│  CLI /  │────▶│   Redis   │────▶│  Rust Crawler │────▶│  Redis   │
│ Batch   │     │  Queue    │     │  (Concurrent) │     │  Stream  │
└─────────┘     └───────────┘     └───────────────┘     └────┬─────┘
                                                             │
                                                             ▼
┌──────────┐    ┌───────────┐     ┌───────────────┐     ┌──────────┐
│ Grafana  │◀───│Prometheus │◀────│  Python       │◀────│  Worker  │
│Dashboard │    │  Metrics  │     │  Workers (N)  │     │  Pool    │
└──────────┘    └───────────┘     └───────┬───────┘     └──────────┘
                                          │
                                          ▼
                                    ┌──────────┐
                                    │PostgreSQL│
                                    │ Database │
                                    └──────────┘
```

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourorg/techdetector.git
cd techdetector

# Local development with Docker Compose
cd docker && docker-compose up -d && cd ..

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python -m techdetector init-db

# Enqueue domains and start processing
python -m techdetector enqueue domains.txt
python -m techdetector.workers.main

# Monitor the pipeline
python scripts/monitor.py
```

## Kubernetes Deployment

```bash
# Deploy with Helm
helm install techdetector ./helm -f ./helm/values-staging.yaml

# Or with Kustomize
kubectl apply -k k8s/overlays/staging/
```

## Monitoring

Access Grafana at `http://grafana.your-cluster/d/techdetector` to view:

- Crawl throughput (requests/sec)
- Queue depth and backlog
- Detection rates by vector
- Worker processing latency (p99)
- Error rates and alerts

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design decisions |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment guide for staging and production |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |
| [RUNBOOKS.md](RUNBOOKS.md) | Operational runbooks for incidents |
| [API.md](API.md) | CLI and internal API reference |

## Testing

```bash
# Run full Python test suite
pytest tests/ -v --cov=techdetector

# Run Rust tests
cd rust_crawler && cargo test

# Run linters
ruff check techdetector/
black --check techdetector/
cd rust_crawler && cargo clippy -- -D warnings
```

## License

Proprietary. All rights reserved.
