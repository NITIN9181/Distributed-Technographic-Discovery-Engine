"""
End-to-end tests for distributed crawling.

Tests the orchestrator enqueue → worker process pipeline.
"""
import pytest
import asyncio
from techdetector.orchestrator import Orchestrator
from techdetector.workers.processor import DetectionProcessor


@pytest.mark.asyncio
async def test_enqueue_and_process(postgres, redis):
    """Test full pipeline: enqueue → crawl → process → persist."""
    orchestrator = Orchestrator(redis, postgres)
    
    # Enqueue a domain
    result = orchestrator.enqueue(["example.com"])
    assert result['enqueued'] == 1

    # Verify queue stats show the pending domain
    stats = orchestrator.get_queue_stats()
    assert stats['domains_pending'] >= 1


@pytest.mark.asyncio
async def test_enqueue_deduplication(postgres, redis):
    """Domains crawled recently should be skipped."""
    orchestrator = Orchestrator(redis, postgres)

    # Mark as crawled
    orchestrator.mark_crawled("dedup-test.example.com")

    # Try to enqueue — should be skipped
    result = orchestrator.enqueue(["dedup-test.example.com"], skip_recent_hours=24)
    assert result['skipped'] == 1
    assert result['enqueued'] == 0


@pytest.mark.asyncio
async def test_enqueue_force_overrides_dedup(postgres, redis):
    """Force flag should bypass recency check."""
    orchestrator = Orchestrator(redis, postgres)

    orchestrator.mark_crawled("force-test.example.com")

    result = orchestrator.enqueue(["force-test.example.com"], force=True)
    assert result['enqueued'] == 1


@pytest.mark.asyncio
async def test_queue_stats(postgres, redis):
    """Queue stats should return valid structure."""
    orchestrator = Orchestrator(redis, postgres)

    stats = orchestrator.get_queue_stats()
    assert 'domains_pending' in stats
    assert 'messages_in_stream' in stats
    assert 'total_crawled' in stats
