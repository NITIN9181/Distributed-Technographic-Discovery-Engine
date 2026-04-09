"""
SQLite persistence layer for the technographic scanner.

Manages the database schema and provides CRUD operations for
companies and their detected technologies.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from techdetector.models import Detection, DetectionVector, ScanResult, Technology

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path("./data/techdetector.db")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    domain TEXT PRIMARY KEY,
    first_scanned_at TIMESTAMP NOT NULL,
    last_scanned_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    technology_id TEXT NOT NULL,
    technology_name TEXT NOT NULL,
    category TEXT NOT NULL,
    detection_vector TEXT NOT NULL,
    evidence TEXT,
    first_detected_at TIMESTAMP NOT NULL,
    last_verified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (domain) REFERENCES companies(domain),
    UNIQUE(domain, technology_id)
);
"""


def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create the database and tables if they don't exist.

    Args:
        db_path: Path to the SQLite database file.
                 Defaults to ``./data/techdetector.db``.

    Returns:
        An open sqlite3.Connection.
    """
    path = Path(db_path) if db_path else _DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing database at %s", path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn


def save_scan_result(conn: sqlite3.Connection, result: ScanResult) -> None:
    """Insert or update a company and its detections.

    On re-scan: updates ``last_scanned_at`` for the company and
    ``last_verified_at`` for existing technologies.  New technologies
    are inserted.

    Args:
        conn: Open database connection.
        result: The ScanResult to persist.
    """
    now = result.scan_timestamp.isoformat()

    # Upsert company
    conn.execute(
        """
        INSERT INTO companies (domain, first_scanned_at, last_scanned_at)
        VALUES (?, ?, ?)
        ON CONFLICT(domain) DO UPDATE SET last_scanned_at = excluded.last_scanned_at
        """,
        (result.domain, now, now),
    )

    # Upsert detections
    for det in result.detections:
        conn.execute(
            """
            INSERT INTO detections
                (domain, technology_id, technology_name, category,
                 detection_vector, evidence, first_detected_at, last_verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain, technology_id) DO UPDATE SET
                last_verified_at = excluded.last_verified_at,
                evidence = excluded.evidence,
                detection_vector = excluded.detection_vector
            """,
            (
                result.domain,
                det.technology.id,
                det.technology.name,
                det.technology.category,
                det.vector.value,
                det.evidence,
                now,
                now,
            ),
        )

    conn.commit()
    logger.info(
        "Saved %d detections for %s", len(result.detections), result.domain
    )


def get_company_technologies(
    conn: sqlite3.Connection, domain: str
) -> list[Detection]:
    """Retrieve all detected technologies for a domain.

    Args:
        conn: Open database connection.
        domain: The domain to query.

    Returns:
        List of Detection objects from the database.
    """
    rows = conn.execute(
        """
        SELECT technology_id, technology_name, category,
               detection_vector, evidence, first_detected_at, last_verified_at
        FROM detections
        WHERE domain = ?
        ORDER BY category, technology_name
        """,
        (domain,),
    ).fetchall()

    detections: list[Detection] = []
    for row in rows:
        tech = Technology(
            id=row["technology_id"],
            name=row["technology_name"],
            category=row["category"],
        )
        detections.append(
            Detection(
                technology=tech,
                vector=DetectionVector(row["detection_vector"]),
                evidence=row["evidence"] or "",
                detected_at=datetime.fromisoformat(row["last_verified_at"]),
            )
        )

    return detections


def get_all_companies(conn: sqlite3.Connection) -> list[dict]:
    """List all scanned companies with scan timestamps.

    Args:
        conn: Open database connection.

    Returns:
        List of dicts with domain, first_scanned_at, and last_scanned_at.
    """
    rows = conn.execute(
        "SELECT domain, first_scanned_at, last_scanned_at FROM companies ORDER BY domain"
    ).fetchall()

    return [
        {
            "domain": row["domain"],
            "first_scanned_at": row["first_scanned_at"],
            "last_scanned_at": row["last_scanned_at"],
        }
        for row in rows
    ]
