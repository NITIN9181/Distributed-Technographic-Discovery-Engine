#!/usr/bin/env python
"""
Database migration runner.

Usage:
    python migrations/migrate.py
    python migrations/migrate.py --rollback 001
"""
import os
import sys
from pathlib import Path
import psycopg2


def run_migrations(db_url: str):
    """Apply all pending SQL migrations in order."""
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Create migrations tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(10) PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()

    # Get already-applied migrations
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
    applied = {row[0] for row in cursor.fetchall()}

    # Run pending migrations
    migrations_dir = Path(__file__).parent
    for migration_file in sorted(migrations_dir.glob("*.sql")):
        version = migration_file.stem.split("_")[0]
        if version not in applied:
            print(f"Applying migration {migration_file.name}...")
            cursor.execute(migration_file.read_text())
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,)
            )
            conn.commit()
            print(f"  ✓ Applied {version}")

    conn.close()
    print("All migrations applied!")


def rollback_migration(db_url: str, version: str):
    """Remove a migration record (does NOT reverse the SQL)."""
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM schema_migrations WHERE version = %s",
        (version,)
    )
    conn.commit()
    conn.close()
    print(f"Rolled back migration record for version {version}")
    print("NOTE: The SQL changes were NOT reversed. Manual intervention required.")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL environment variable required")
        sys.exit(1)

    if len(sys.argv) > 2 and sys.argv[1] == "--rollback":
        rollback_migration(db_url, sys.argv[2])
    else:
        run_migrations(db_url)
