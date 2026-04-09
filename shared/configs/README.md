# Shared Configurations

This directory will contain shared configuration files used across the
Distributed Technographic Discovery Engine components.

## Planned Contents

| File | Purpose |
|------|---------|
| `kafka.toml` | Kafka broker addresses, topic names, consumer group IDs |
| `postgres.toml` | Database connection strings, pool sizes, migration settings |
| `crawler.toml` | Rate limits, user-agent strings, timeout values |
| `logging.toml` | Log levels, output formats, and destinations |

## Configuration Strategy

We use TOML as our configuration format because:
- It's natively supported by Rust (serde + toml crate)
- It's easy to parse in Python (tomllib in 3.11+)
- It's human-readable and supports comments (unlike JSON)
- It handles nested structures well (unlike .env files)
