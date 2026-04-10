# Troubleshooting Guide

## Common Issues

### Workers not processing messages

**Symptoms:** Queue depth increasing, no worker logs.

**Check:**
1. Verify workers are running: `kubectl get pods -l app=worker`
2. Check worker logs: `kubectl logs -l app=worker --tail=50`
3. Verify Redis connectivity from worker:
   ```bash
   kubectl exec -it <worker-pod> -- python -c "import redis; r=redis.from_url('redis://redis:6379'); print(r.ping())"
   ```
4. Check consumer group exists:
   ```bash
   redis-cli XINFO GROUPS crawl:results
   ```

**Common fixes:**
- Restart workers: `kubectl rollout restart deployment worker`
- Reset consumer group if corrupted:
  ```bash
  redis-cli XGROUP DESTROY crawl:results techdetector_workers
  ```

---

### Crawler not fetching domains

**Symptoms:** `domains:pending` queue has items but no crawl results.

**Check:**
1. Verify crawler is running: `kubectl get pods -l app=crawler`
2. Check crawler logs: `kubectl logs -l app=crawler --tail=50`
3. Test Redis pop from crawler:
   ```bash
   redis-cli LLEN domains:pending
   ```

**Common fixes:**
- Network issues: Check DNS resolution from crawler pod
- Rate limiting: Check if domains are being rate-limited
- Memory: Increase crawler memory limits if OOMKilled

---

### Database connection failures

**Symptoms:** `psycopg2.OperationalError: could not connect to server`

**Check:**
1. Verify PostgreSQL is running: `kubectl get pods -l app=postgres`
2. Test connection:
   ```bash
   kubectl exec -it <postgres-pod> -- pg_isready -U techdetector
   ```
3. Check secret values:
   ```bash
   kubectl get secret techdetector-secrets -o jsonpath='{.data.DATABASE_URL}' | base64 -d
   ```

**Common fixes:**
- Restart PostgreSQL: `kubectl rollout restart statefulset postgres`
- Check PVC status: `kubectl get pvc`

---

### High error rate in workers

**Symptoms:** Grafana shows error rate > 5%.

**Check:**
1. Check worker logs for stack traces
2. Common errors:
   - `spacy` model not loaded → ensure `en_core_web_sm` is in the Docker image
   - JSON parse errors → crawler publishing malformed data
   - Database constraint violations → duplicate detection logic

**Common fixes:**
- Check if signatures.json is valid JSON
- Verify the crawl message schema matches what workers expect

---

### Metrics endpoint not responding

**Symptoms:** Prometheus targets show as DOWN.

**Check:**
1. Port-forward and test: `kubectl port-forward <pod> 9090:9090 && curl localhost:9090/metrics`
2. Check if metrics port is exposed in the Deployment spec
3. Verify Prometheus scrape annotations on pods

---

### Out of memory (OOMKilled)

**Symptoms:** Pods restarting with `OOMKilled` status.

**Check:**
```bash
kubectl describe pod <pod-name> | grep -A5 "Last State"
```

**Fix:**
- Increase memory limits in `values.yaml` or Kustomize overlay
- For workers: reduce batch size via `WORKER_BATCH_SIZE` env var
- For crawlers: reduce `MAX_CONCURRENT` connections

---

### Redis memory issues

**Symptoms:** Redis refusing writes, `OOM command not allowed when used memory > maxmemory`.

**Check:**
```bash
redis-cli INFO memory
redis-cli XLEN crawl:results
redis-cli LLEN domains:pending
```

**Fix:**
- Trim the stream: `redis-cli XTRIM crawl:results MAXLEN ~ 100000`
- Increase Redis memory limits
- Scale up workers to process messages faster

## Health Check Endpoints

| Service | Endpoint | Expected |
|---------|----------|----------|
| Crawler | `:9090/health` | `200 OK` |
| Worker | `:8080/health` | `{"status": "healthy"}` |
| Crawler | `:9090/metrics` | Prometheus text format |
| Worker | `:9090/metrics` | Prometheus text format |
