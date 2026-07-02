"""SQLite database adapter."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from base_db import BaseDatabaseAdapter
from init_db import DB_PATH, create_database


class SQLiteAdapter(BaseDatabaseAdapter):
    """SQLite-backed database adapter with safe query building."""

    backend_name = "sqlite"

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        if not self.db_path.exists():
            create_database(self.db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def database_label(self) -> str:
        return str(self.db_path)

    def _placeholder(self) -> str:
        return "?"

    def list_tables(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def _get_table_schema_impl(self, table: str) -> dict[str, Any]:
        with self.connect() as conn:
            columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
            foreign_keys = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()

        return {
            "table": table,
            "columns": [
                {
                    "name": col["name"],
                    "type": col["type"],
                    "not_null": bool(col["notnull"]),
                    "primary_key": bool(col["pk"]),
                    "default": col["dflt_value"],
                }
                for col in columns
            ],
            "foreign_keys": [
                {
                    "column": fk["from"],
                    "references_table": fk["table"],
                    "references_column": fk["to"],
                }
                for fk in foreign_keys
            ],
        }

    def _execute_insert_and_fetch(
        self,
        table: str,
        columns: list[str],
        params: list[Any],
    ) -> dict[str, Any]:
        column_sql = ", ".join(columns)
        placeholders = self._placeholders(len(columns))
        query = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"

        with self.connect() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            row_id = cursor.lastrowid
            inserted = conn.execute(
                f"SELECT * FROM {table} WHERE rowid = {self._placeholder()}",
                (row_id,),
            ).fetchone()

        if inserted is not None:
            return dict(inserted)
        return {"id": row_id, **dict(zip(columns, params, strict=True))}
