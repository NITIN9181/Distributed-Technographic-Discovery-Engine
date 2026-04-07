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
