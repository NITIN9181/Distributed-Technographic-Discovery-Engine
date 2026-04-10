import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    database_url: str
    redis_url: str
    spacy_model: str = "en_core_web_sm"
    dns_timeout: float = 5.0
    http_timeout: float = 15.0

    # Crawler settings
    crawler_max_concurrent: int = 500
    crawler_timeout_seconds: int = 15

    # Worker settings
    worker_batch_size: int = 10
    worker_health_port: int = 8080

    # Rate limits and behavior (legacy/legacy mappings)
    batch_concurrency: int = 10
    rate_limit_per_domain: float = 2.0
    rate_limit_burst: float = 5.0
    respect_robots: bool = True
    skip_recent_hours: int = 24
    retry_count: int = 3


def load_config() -> Config:
    load_dotenv()
    return Config(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://techdetector:localdev123@localhost:5432/techdetector",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        crawler_max_concurrent=int(os.getenv("MAX_CONCURRENT", "500")),
        spacy_model=os.getenv("SPACY_MODEL", "en_core_web_sm"),
        dns_timeout=float(os.getenv("DNS_TIMEOUT", "5.0")),
        http_timeout=float(os.getenv("HTTP_TIMEOUT", "15.0")),
        batch_concurrency=int(os.getenv("BATCH_CONCURRENCY", "10")),
        rate_limit_per_domain=float(os.getenv("RATE_LIMIT_PER_DOMAIN", "2.0")),
        rate_limit_burst=float(os.getenv("RATE_LIMIT_BURST", "5.0")),
        respect_robots=os.getenv("RESPECT_ROBOTS", "true").lower() == "true",
        skip_recent_hours=int(os.getenv("SKIP_RECENT_HOURS", "24")),
        retry_count=int(os.getenv("RETRY_COUNT", "3")),
    )
