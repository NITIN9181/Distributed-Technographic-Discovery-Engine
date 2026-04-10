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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

async def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    db_url = os.getenv("DATABASE_URL", "postgresql://techdetector:localdev123@localhost:5432/techdetector")
    
    # Ensure DB is active. The crawler handles getting the domains, worker handles detections.
    init_database()
    
    processor = DetectionProcessor(redis_url, db_url)
    health = HealthServer(redis_url, port=int(os.getenv("WORKER_HEALTH_PORT", 8080)))
    
    await asyncio.gather(
        processor.run(),
        health.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
