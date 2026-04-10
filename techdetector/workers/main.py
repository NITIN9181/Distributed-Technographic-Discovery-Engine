"""
Worker entry point.

Usage:
    python -m techdetector.workers.main
"""

import asyncio
import os
import logging
from .processor import DetectionProcessor
from .health import HealthServer
from ..scanner import init_database
from ..metrics import start_metrics_server

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


async def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://techdetector:localdev123@localhost:5432/techdetector",
    )
    metrics_port = int(os.getenv("METRICS_PORT", "9090"))

    # Ensure DB is active. The crawler handles getting the domains, worker handles detections.
    init_database()

    # Start Prometheus metrics endpoint
    start_metrics_server(metrics_port)
    logging.info(f"Prometheus metrics server started on port {metrics_port}")

    # Start health server first in a background task
    health_port = int(os.getenv("WORKER_HEALTH_PORT", 8080))
    health = HealthServer(redis_url, port=health_port)
    health_task = asyncio.create_task(health.run())
    logging.info(f"Health server started on port {health_port}")

    # Initialize processor in a thread to avoid blocking the event loop (model loading is heavy)
    processor = await asyncio.to_thread(DetectionProcessor, redis_url, db_url)
    logging.info("DetectionProcessor initialized")
    
    await processor.run()
    await health_task


if __name__ == "__main__":
    asyncio.run(main())
