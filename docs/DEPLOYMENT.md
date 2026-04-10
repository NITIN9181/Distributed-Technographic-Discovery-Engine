# Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- Kubernetes 1.28+ cluster (for K8s deployment)
- Helm 3 (for Helm deployment)
- `kubectl` configured with cluster access

## Local Development

### Docker Compose

```bash
# Start infrastructure (Postgres, Redis, Crawler, Workers)
cd docker
docker-compose up -d

# Verify services are healthy
docker-compose ps

# View logs
docker-compose logs -f crawler
docker-compose logs -f worker
```

### Manual Setup

```bash
# Install Python deps
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://techdetector:localdev123@localhost:5432/techdetector"
export REDIS_URL="redis://localhost:6379"

# Initialize database
python -m techdetector init-db

# Run database migrations
python migrations/migrate.py

# Start workers
python -m techdetector.workers.main

# Enqueue domains
python -m techdetector enqueue domains.txt
```

## Staging Deployment

### Kustomize

```bash
# Review what will be applied
kubectl apply -k k8s/overlays/staging/ --dry-run=client

# Apply
kubectl apply -k k8s/overlays/staging/

# Verify
kubectl get pods -n techdetector-staging
```

### Helm

```bash
helm upgrade --install techdetector ./helm \
  -f ./helm/values-staging.yaml \
  --set postgresql.auth.password=YOUR_STAGING_PASSWORD \
  --set redis.auth.password=YOUR_STAGING_REDIS_PASSWORD \
  --namespace techdetector-staging \
  --create-namespace
```

## Production Deployment

### Pre-deployment Checklist

- [ ] All CI checks pass on the release tag
- [ ] Staging deployment verified
- [ ] Database migrations tested on staging
- [ ] Rollback plan documented
- [ ] On-call engineer notified

### Deploy

```bash
# Tag a release
git tag v1.0.0
git push origin v1.0.0

# The CD pipeline will automatically:
# 1. Build and push Docker images to GHCR
# 2. Deploy to staging
# 3. Deploy to production (on v* tags)
```

### Manual Helm Deploy

```bash
helm upgrade --install techdetector ./helm \
  -f ./helm/values-production.yaml \
  --set image.tag=v1.0.0 \
  --set postgresql.auth.password=$PROD_PG_PASSWORD \
  --set redis.auth.password=$PROD_REDIS_PASSWORD \
  --namespace techdetector-production \
  --create-namespace
```

## Database Migrations

```bash
# Run pending migrations
DATABASE_URL="postgresql://..." python migrations/migrate.py

# Rollback a migration record (SQL is NOT reversed)
DATABASE_URL="postgresql://..." python migrations/migrate.py --rollback 002
```

## Monitoring Setup

### Prometheus

The crawler and worker pods expose metrics at `:9090/metrics`. Prometheus is configured
to auto-discover pods via Kubernetes service discovery annotations:

```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "9090"
```

### Grafana

Import the dashboard from `k8s/monitoring/grafana-dashboards/techdetector.json`
or configure auto-provisioning via ConfigMap.

### Alerts

Configure Alertmanager receivers in `k8s/monitoring/alertmanager-config.yaml`:
- Slack webhook for warnings
- PagerDuty for critical alerts

## Scaling

```bash
# Scale workers
kubectl scale deployment worker --replicas=10 -n techdetector-production

# Scale crawlers
kubectl scale deployment crawler --replicas=4 -n techdetector-production
```
