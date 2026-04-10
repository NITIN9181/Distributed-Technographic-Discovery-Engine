#!/usr/bin/env python
"""
Monitor crawl progress in real-time.

Usage:
    python scripts/monitor.py
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.live import Live
from rich.table import Table
from rich.console import Console

from techdetector.orchestrator import Orchestrator
from techdetector.config import load_config

def create_table(stats: dict) -> Table:
    table = Table(title="TechDetector Crawl Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Domains Pending", str(stats['domains_pending']))
    table.add_row("Messages in Stream", str(stats['messages_in_stream']))
    table.add_row("Messages Pending ACK", str(stats['messages_pending_ack']))
    table.add_row("Total Crawled (all time)", str(stats['total_crawled']))
    
    return table

def main():
    config = load_config()
    orchestrator = Orchestrator(config.redis_url, config.database_url)
    console = Console()
    
    with Live(create_table(orchestrator.get_queue_stats()), refresh_per_second=1) as live:
        while True:
            try:
                stats = orchestrator.get_queue_stats()
                live.update(create_table(stats))
                time.sleep(1)
            except KeyboardInterrupt:
                break

if __name__ == '__main__':
    main()
