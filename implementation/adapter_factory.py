"""Create the configured database adapter (SQLite or PostgreSQL)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from base_db import BaseDatabaseAdapter


def create_adapter() -> BaseDatabaseAdapter:
    backend = os.getenv("DB_BACKEND", "sqlite").strip().lower()

    if backend in {"postgres", "postgresql"}:
        connection_url = os.getenv("DATABASE_URL")
        if not connection_url:
            raise ValueError(
                "DB_BACKEND=postgresql requires DATABASE_URL, "
                "e.g. postgresql://user:pass@localhost:5432/sqlite_lab"
            )
        from postgres_db import PostgreSQLAdapter

        return PostgreSQLAdapter(connection_url)

    from db import SQLiteAdapter

    db_path = os.getenv("SQLITE_DB_PATH")
    return SQLiteAdapter(db_path)
