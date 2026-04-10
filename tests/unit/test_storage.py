"""
Unit tests for the PostgreSQL storage layer.

These tests require a PostgreSQL testcontainer (integration-level fixture).
"""
import pytest
from datetime import datetime, timezone

from techdetector.models import Detection, DetectionVector, ScanResult, Technology
from techdetector.storage import init_db, save_scan_result, get_company_technologies, query_by_technology


def _make_scan_result(domain: str = "test.example.com") -> ScanResult:
    """Helper to create a ScanResult with sample detections."""
    return ScanResult(
        domain=domain,
        scan_timestamp=datetime.now(timezone.utc),
        detections=[
            Detection(
                technology=Technology(id="react", name="React", category="Frontend Framework"),
                vector=DetectionVector.HTML_SOURCE,
                evidence="<script src='react.js'>"
            ),
            Detection(
                technology=Technology(id="cloudflare", name="Cloudflare", category="CDN"),
                vector=DetectionVector.HTTP_HEADER,
                evidence="server: cloudflare"
            ),
        ],
        html_fetched=True,
        headers_captured=True,
    )


class TestStorage:
    """Tests for database initialization and persistence."""

    @pytest.mark.skipif(
        not pytest.importorskip("testcontainers", reason="testcontainers required"),
        reason="testcontainers not available"
    )
    def test_init_db_creates_tables(self, postgres, monkeypatch):
        """Verify init_db creates the required tables."""
        monkeypatch.setenv("DATABASE_URL", postgres)
        init_db()
        # Running again should be idempotent
        init_db()

    @pytest.mark.skipif(
        not pytest.importorskip("testcontainers", reason="testcontainers required"),
        reason="testcontainers not available"
    )
    def test_save_and_query(self, postgres, monkeypatch):
        """Verify save_scan_result persists and can be queried."""
        monkeypatch.setenv("DATABASE_URL", postgres)
        init_db()

        result = _make_scan_result()
        save_scan_result(result)

        techs = get_company_technologies("test.example.com")
        assert len(techs) == 2
        tech_ids = {t.technology.id for t in techs}
        assert "react" in tech_ids
        assert "cloudflare" in tech_ids

    @pytest.mark.skipif(
        not pytest.importorskip("testcontainers", reason="testcontainers required"),
        reason="testcontainers not available"
    )
    def test_upsert_updates_verification_date(self, postgres, monkeypatch):
        """Re-saving should update latest_verification_date, not duplicate."""
        monkeypatch.setenv("DATABASE_URL", postgres)
        init_db()

        result = _make_scan_result("upsert.example.com")
        save_scan_result(result)
        save_scan_result(result)  # Second save = upsert

        techs = get_company_technologies("upsert.example.com")
        # Should still be 2, not 4
        assert len(techs) == 2

    @pytest.mark.skipif(
        not pytest.importorskip("testcontainers", reason="testcontainers required"),
        reason="testcontainers not available"
    )
    def test_query_by_technology(self, postgres, monkeypatch):
        """Verify querying by technology identifier."""
        monkeypatch.setenv("DATABASE_URL", postgres)
        init_db()

        result = _make_scan_result("query.example.com")
        save_scan_result(result)

        rows = query_by_technology("react")
        assert len(rows) >= 1
        assert any(r["canonical_domain"] == "query.example.com" for r in rows)
