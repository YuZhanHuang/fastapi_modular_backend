"""Run Alembic migrations with a PostgreSQL advisory lock."""

from __future__ import annotations

import os
import subprocess
import sys
import time

from sqlalchemy import create_engine, text

LOCK_ID = 737001


def _repair_orphaned_alembic_type(connection) -> None:
    """Drop stale alembic_version composite type left by a failed concurrent migration."""
    table_exists = connection.execute(
        text("SELECT to_regclass('public.alembic_version') IS NOT NULL")
    ).scalar()
    if table_exists:
        return

    type_exists = connection.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = 'alembic_version'
                  AND n.nspname = 'public'
            )
            """
        )
    ).scalar()
    if type_exists:
        print("[run_migrations] Removing orphaned alembic_version type...")
        connection.execute(text("DROP TYPE IF EXISTS alembic_version CASCADE"))


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    timeout_seconds = int(os.environ.get("MIGRATION_LOCK_TIMEOUT", "120"))
    engine = create_engine(database_url, isolation_level="AUTOCOMMIT")

    for attempt in range(timeout_seconds):
        with engine.connect() as connection:
            locked = connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": LOCK_ID},
            ).scalar()

            if not locked:
                if attempt == 0:
                    print("[run_migrations] Another process is running migrations, waiting...")
                time.sleep(1)
                continue

            try:
                _repair_orphaned_alembic_type(connection)
                print("[run_migrations] Running alembic upgrade head...")
                subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)
                print("[run_migrations] Migrations complete")
                return
            finally:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": LOCK_ID},
                )

    print("[run_migrations] Timed out waiting for migration lock", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
