#!/usr/bin/env python
"""
Enqueue domains for crawling.

Usage:
    python scripts/enqueue_domains.py domains.txt
    python scripts/enqueue_domains.py --stdin < domains.txt
    echo "stripe.com" | python scripts/enqueue_domains.py --stdin
"""
import argparse
import sys
import os

# Add the project root to sys.path so we can import techdetector modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from techdetector.orchestrator import Orchestrator
from techdetector.config import load_config

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?', help='File with domains')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin')
    parser.add_argument('--force', action='store_true', help='Ignore recency check')
    args = parser.parse_args()
    
    config = load_config()
    orchestrator = Orchestrator(config.redis_url, config.database_url)
    
    if args.stdin or not args.file:
        domains = [line.strip() for line in sys.stdin if line.strip()]
    else:
        with open(args.file) as f:
            domains = [line.strip() for line in f if line.strip()]
    
    result = orchestrator.enqueue(domains, force=args.force)
    print(f"Enqueued: {result['enqueued']}, Skipped: {result['skipped']}")

if __name__ == '__main__':
    main()
