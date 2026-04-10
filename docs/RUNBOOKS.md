# Operational Runbooks

## Runbook: High Error Rate Alert

**Alert:** `HighErrorRate` — Worker error rate > 5% for 5 minutes.

### Steps

1. **Assess severity:**
   ```bash
   # Check current error rate
   kubectl exec -it <prometheus-pod> -- promtool query instant \
     'sum(rate(techdetector_messages_processed_total{status="error"}[5m])) / sum(rate(techdetector_messages_processed_total[5m]))'
   ```

2. **Check worker logs for error patterns:**
   ```bash
   kubectl logs -l app=worker --tail=100 | grep ERROR
   ```

3. **Common causes:**
   - Database connection timeout → check Postgres health
   - Malformed crawl messages → check crawler output
   - spaCy model missing → rebuild worker image

4. **Mitigate:**
   - If DB-related: `kubectl rollout restart statefulset postgres`
   - If message-related: skip bad messages by acknowledging them
   - Scale workers: `kubectl scale deployment worker --replicas=15`

5. **Verify recovery:** Error rate should drop below 5% within 5 minutes.

---

## Runbook: Queue Backlog Alert

**Alert:** `QueueBacklog` — More than 10,000 domains pending for 10+ minutes.

### Steps

1. **Check queue depth:**
   ```bash
   redis-cli LLEN domains:pending
   redis-cli XLEN crawl:results
   ```

2. **Check crawler throughput:**
   ```bash
   # Crawl rate from Prometheus
   curl -s http://prometheus:9090/api/v1/query?query=rate(crawler_requests_total[5m])
   ```

3. **Scale up:**
   ```bash
   kubectl scale deployment crawler --replicas=6
   kubectl scale deployment worker --replicas=15
   ```

4. **If crawlers are stuck:**
   ```bash
   kubectl rollout restart deployment crawler
   ```

5. **Monitor until queue drains below 1000.**

---

## Runbook: Worker/Crawler Down Alert

**Alert:** `WorkerDown` or `CrawlerDown` — Instance unreachable for 2+ minutes.

### Steps

1. **Check pod status:**
   ```bash
   kubectl get pods -l app=worker -o wide
   kubectl get pods -l app=crawler -o wide
   ```

2. **Check for OOMKilled or CrashLoopBackOff:**
   ```bash
   kubectl describe pod <pod-name>
   ```

3. **If OOMKilled:** Increase memory limits and redeploy.

4. **If CrashLoopBackOff:** Check logs for startup errors:
   ```bash
   kubectl logs <pod-name> --previous
   ```

5. **Force restart:**
   ```bash
   kubectl rollout restart deployment <worker|crawler>
   ```

---

## Runbook: Database Disk Full

### Steps

1. **Check disk usage:**
   ```bash
   kubectl exec -it <postgres-pod> -- df -h /var/lib/postgresql/data
   ```

2. **Check table sizes:**
   ```sql
   SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
   FROM pg_catalog.pg_statio_user_tables
   ORDER BY pg_total_relation_size(relid) DESC;
   ```

3. **If technology_installations is too large:**
   ```sql
   -- Archive old detections (older than 90 days of no verification)
   DELETE FROM technology_installations
   WHERE latest_verification_date < NOW() - INTERVAL '90 days';
   ```

4. **Expand PVC if possible:**
   ```bash
   kubectl edit pvc postgres-data-postgres-0
   # Increase spec.resources.requests.storage
   ```

---

## Runbook: Redis Memory Pressure

### Steps

1. **Check memory usage:**
   ```bash
   redis-cli INFO memory | grep used_memory_human
   redis-cli XLEN crawl:results
   ```

2. **Trim stream if too long:**
   ```bash
   redis-cli XTRIM crawl:results MAXLEN ~ 50000
   ```

3. **Clear stale rate limit keys:**
   ```bash
   redis-cli KEYS "ratelimit:*" | head -20
   # If thousands exist:
   redis-cli KEYS "ratelimit:*" | xargs redis-cli DEL
   ```

4. **Scale workers to process backlog faster.**

---

## Runbook: Rolling Deployment

### Steps

1. **Tag the release:**
   ```bash
   git tag v1.x.x && git push origin v1.x.x
   ```

2. **Monitor the CD pipeline** in GitHub Actions.

3. **Verify staging deployment:**
   ```bash
   kubectl get pods -n techdetector-staging
   kubectl logs -l app=worker -n techdetector-staging --tail=20
   ```

4. **Verify production deployment** (automated on v* tags):
   ```bash
   kubectl get pods -n techdetector-production
   ```

5. **Check Grafana** for any anomalies post-deploy.

6. **Rollback if needed:**
   ```bash
   helm rollback techdetector 1 -n techdetector-production
   ```
