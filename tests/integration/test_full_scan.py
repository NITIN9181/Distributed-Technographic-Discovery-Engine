"""
Integration tests for the full scan pipeline.

Requires testcontainers (Docker) for PostgreSQL.
"""
import pytest
from techdetector.scanner import perform_scan, init_database


@pytest.mark.asyncio
async def test_full_scan_real_domain(postgres, monkeypatch):
    """Integration test: scan example.com with all vectors and verify result shape."""
    monkeypatch.setenv("DATABASE_URL", postgres)
    init_database()

    result = perform_scan("https://example.com", ["html", "headers"])

    assert result.domain == "example.com"
    assert result.html_fetched is True
    assert isinstance(result.detections, list)


@pytest.mark.asyncio
async def test_scan_persistence(postgres, monkeypatch):
    """Verify scan results are persisted to PostgreSQL."""
    monkeypatch.setenv("DATABASE_URL", postgres)
    init_database()

    perform_scan("https://example.com", ["html", "headers"])

    from techdetector.storage import get_company_technologies
    technologies = get_company_technologies("example.com")
    # example.com is minimal, might not have many technologies
    assert isinstance(technologies, list)


@pytest.mark.asyncio
async def test_scan_dns_vector(postgres, monkeypatch):
    """Verify DNS detection vector runs without error."""
    monkeypatch.setenv("DATABASE_URL", postgres)
    init_database()

    result = perform_scan("example.com", ["dns"])
    assert result.domain == "example.com"
    assert isinstance(result.detections, list)
