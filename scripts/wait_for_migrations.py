"""Wait until Alembic migrations have been applied by another service."""

from __future__ import annotations

import os
import sys
import time

from sqlalchemy import create_engine, text


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    timeout_seconds = int(os.environ.get("MIGRATION_WAIT_TIMEOUT", "120"))
    engine = create_engine(database_url)

    for attempt in range(timeout_seconds):
        try:
            with engine.connect() as connection:
                exists = connection.execute(
                    text("SELECT to_regclass('public.alembic_version') IS NOT NULL")
                ).scalar()
                if exists:
                    print("[wait_for_migrations] alembic_version table is ready")
                    return
        except Exception:
            pass

        if attempt == 0:
            print("[wait_for_migrations] Waiting for database migrations...")
        time.sleep(1)

    print("[wait_for_migrations] Timed out waiting for migrations", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
