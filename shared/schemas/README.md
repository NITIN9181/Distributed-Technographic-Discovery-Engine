# Shared Schemas

This directory will contain shared data schemas used by both the Rust crawler
and the Python processor to ensure consistent data contracts across the pipeline.

## Planned Contents

| File | Purpose |
|------|---------|
| `crawl_result.json` | JSON Schema for crawler output (URL, headers, body hash, TLS info) |
| `tech_signal.json` | JSON Schema for detected technology signals |
| `domain_profile.json` | JSON Schema for aggregated domain technographic profiles |
| `kafka_events.json` | Avro/JSON schemas for Kafka message formats |

## Why Shared Schemas?

The crawler (Rust) produces data that the processor (Python) consumes via Kafka.
Shared schemas ensure:

1. **Data contract enforcement** — Both sides agree on field names, types, and required fields
2. **Schema evolution** — We can version schemas and handle backward compatibility
3. **Documentation** — Schemas serve as living documentation of our data model
4. **Validation** — Both Rust (serde) and Python (pydantic) can validate against these schemas
