import sqlite3
import psycopg2
import logging
from config import load_config
from psycopg2.extras import execute_values
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    sqlite_path = Path(__file__).parent.parent / "data" / "techdetector.db"
    
    if not sqlite_path.exists():
        logger.info(f"No SQLite database found at {sqlite_path}. Nothing to migrate.")
        return

    config = load_config()
    
    # Read from SQLite
    logger.info("Reading from SQLite...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    companies = sqlite_conn.execute("SELECT * FROM companies").fetchall()
    detections = sqlite_conn.execute("SELECT * FROM detections").fetchall()
    
    # Write to Postgres
    logger.info("Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(config.database_url)
    
    with pg_conn.cursor() as cur:
        logger.info(f"Migrating {len(companies)} companies...")
        
        company_records = [
            (c['domain'], c['domain'], c['last_scanned_at']) 
            for c in companies
        ]
        
        execute_values(
            cur,
            """
            INSERT INTO scanned_companies (canonical_domain, corporate_name, last_successful_crawl)
            VALUES %s
            ON CONFLICT (canonical_domain) DO NOTHING
            """,
            company_records
        )
        
        logger.info(f"Migrating {len(detections)} detections...")
        
        detection_records = []
        for d in detections:
            # Map legacy vectors to new names if needed
            vector = d['detection_vector']
            if vector == 'html_source':
                vector = 'HTML_SOURCE'
            elif vector == 'http_header':
                vector = 'HTTP_HEADER'
            elif vector == 'dns_record':
                vector = 'DNS_RECORD'
            elif vector == 'job_posting':
                vector = 'JOB_POSTING_NLP'
                
            detection_records.append((
                d['domain'],
                d['technology_id'],
                vector,
                d['evidence'],
                d['category'],
                d['first_detected_at'],
                d['last_verified_at']
            ))

        execute_values(
            cur,
            """
            INSERT INTO technology_installations (
                canonical_domain, technology_identifier, detection_vector, 
                evidence, category, initial_detection_date, latest_verification_date
            )
            VALUES %s
            ON CONFLICT (canonical_domain, technology_identifier) DO NOTHING
            """,
            detection_records
        )
        
    pg_conn.commit()
    pg_conn.close()
    sqlite_conn.close()
    logger.info("Migration complete!")

if __name__ == "__main__":
    migrate()
