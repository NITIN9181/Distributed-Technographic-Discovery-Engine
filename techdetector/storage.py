"""
PostgreSQL persistence layer.

Implements the production schema from the spec.
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from techdetector.models import Detection, DetectionVector, ScanResult, Technology
from techdetector.config import load_config

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS scanned_companies (
    canonical_domain VARCHAR(255) PRIMARY KEY,
    corporate_name VARCHAR(255),
    last_successful_crawl TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS technology_installations (
    id SERIAL PRIMARY KEY,
    canonical_domain VARCHAR(255) NOT NULL REFERENCES scanned_companies(canonical_domain),
    technology_identifier VARCHAR(100) NOT NULL,
    detection_vector VARCHAR(50) NOT NULL,
    evidence TEXT,
    category VARCHAR(50),
    initial_detection_date TIMESTAMP NOT NULL DEFAULT NOW(),
    latest_verification_date TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(canonical_domain, technology_identifier)
);

CREATE INDEX IF NOT EXISTS idx_tech_by_vector 
ON technology_installations(detection_vector);

CREATE INDEX IF NOT EXISTS idx_tech_by_tech_id 
ON technology_installations(technology_identifier);
"""


@contextmanager
def get_connection():
    config = load_config()
    conn = psycopg2.connect(config.database_url, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    import psycopg2.errors

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA)
                logger.info("Database tables initialized.")
    except (psycopg2.errors.UniqueViolation, psycopg2.errors.DuplicateTable):
        logger.info("Database tables already initialized (concurrency ignored).")


def save_scan_result(result: ScanResult):
    """
    Upsert company and technology detections.
    On conflict, update latest_verification_date.
    """
    now = result.scan_timestamp

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Upsert company
            cur.execute(
                """
                INSERT INTO scanned_companies (canonical_domain, last_successful_crawl)
                VALUES (%s, %s)
                ON CONFLICT (canonical_domain) 
                DO UPDATE SET last_successful_crawl = EXCLUDED.last_successful_crawl;
                """,
                (result.domain, now),
            )

            # Upsert detections
            for det in result.detections:
                cur.execute(
                    """
                    INSERT INTO technology_installations (
                        canonical_domain, technology_identifier, detection_vector, 
                        evidence, category, initial_detection_date, latest_verification_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (canonical_domain, technology_identifier)
                    DO UPDATE SET 
                        latest_verification_date = EXCLUDED.latest_verification_date,
                        evidence = EXCLUDED.evidence,
                        detection_vector = EXCLUDED.detection_vector;
                    """,
                    (
                        result.domain,
                        det.technology.id,
                        det.vector.name,
                        det.evidence,
                        det.technology.category,
                        now,
                        now,
                    ),
                )

            logger.info(
                f"Saved {len(result.detections)} PostgreSQL detections for {result.domain}"
            )


def query_by_technology(tech_id: str) -> list[dict]:
    """Find all companies using a specific technology."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.canonical_domain, t.technology_identifier as technology_id, 
                       t.detection_vector, t.category, t.evidence, 
                       t.initial_detection_date as first_detected_at, 
                       t.latest_verification_date as last_verified_at,
                       c.last_successful_crawl as last_scanned_at
                FROM technology_installations t
                JOIN scanned_companies c ON t.canonical_domain = c.canonical_domain
                WHERE t.technology_identifier = %s
                ORDER BY t.canonical_domain
                """,
                (tech_id,),
            )
            return cur.fetchall()


def query_by_vector(vector: DetectionVector) -> list[dict]:
    """Find all detections from a specific vector (e.g., JOB_POSTING_NLP)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.canonical_domain, t.technology_identifier as technology_id, 
                       t.detection_vector, t.category, t.evidence, 
                       t.initial_detection_date as first_detected_at, 
                       t.latest_verification_date as last_verified_at
                FROM technology_installations t
                WHERE t.detection_vector = %s
                ORDER BY t.canonical_domain, t.technology_identifier
                """,
                (vector.name,),
            )
            return cur.fetchall()


def get_company_technologies(domain: str) -> list[Detection]:
    """Retrieve all detected technologies for a domain."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT technology_identifier as technology_id, category,
                       detection_vector, evidence, initial_detection_date as first_detected_at, 
                       latest_verification_date as last_verified_at
                FROM technology_installations
                WHERE canonical_domain = %s
                ORDER BY category, technology_identifier
                """,
                (domain,),
            )
            rows = cur.fetchall()

            detections = []
            for row in rows:
                tech = Technology(
                    id=row["technology_id"],
                    name=row["technology_id"]
                    .replace("_", " ")
                    .title(),  # Approximation based on ID if name missing
                    category=row["category"],
                )
                detections.append(
                    Detection(
                        technology=tech,
                        vector=DetectionVector[row["detection_vector"]],
                        evidence=row["evidence"] or "",
                        detected_at=row["last_verified_at"],
                    )
                )

            return detections


def get_company_detections(domain: str) -> list[dict]:
    """Retrieve raw dictionary detections for a domain."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT technology_identifier as technology_id, category,
                       detection_vector, evidence, initial_detection_date as first_detected_at, 
                       latest_verification_date as last_verified_at
                FROM technology_installations
                WHERE canonical_domain = %s
                ORDER BY category, technology_identifier
                """,
                (domain,),
            )
            # psycopg2 RealDictRow -> dict and datetime -> str
            rows = []
            for row in cur.fetchall():
                d = dict(row)
                d["first_detected_at"] = d["first_detected_at"].isoformat()
                d["last_verified_at"] = d["last_verified_at"].isoformat()
                rows.append(d)
            return rows


def query_detections(filters: dict) -> list[dict]:
    """Query detections with optional filters."""
    query = """
        SELECT t.canonical_domain, t.technology_identifier as technology_id, 
               t.detection_vector, t.category, t.evidence, 
               t.initial_detection_date as first_detected_at, 
               t.latest_verification_date as last_verified_at
        FROM technology_installations t
        WHERE 1=1
    """
    params = []

    if filters.get("tech"):
        query += " AND t.technology_identifier = %s"
        params.append(filters["tech"])
    if filters.get("vector"):
        query += " AND t.detection_vector = %s"
        params.append(filters["vector"])
    if filters.get("since"):
        query += " AND t.latest_verification_date >= %s"
        params.append(filters["since"])

    query += " ORDER BY t.canonical_domain, t.technology_identifier"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = []
            for row in cur.fetchall():
                d = dict(row)
                d["first_detected_at"] = d["first_detected_at"].isoformat()
                d["last_verified_at"] = d["last_verified_at"].isoformat()
                rows.append(d)
            return rows


def get_all_companies() -> list[dict]:
    """List all scanned companies with scan timestamps."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT canonical_domain as domain, 
                       last_successful_crawl as first_scanned_at, -- using last as an approximation
                       last_successful_crawl as last_scanned_at
                FROM scanned_companies
                ORDER BY canonical_domain
                """)
            return cur.fetchall()
