"""PostgreSQL database adapter sharing the same MCP query surface."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from base_db import BaseDatabaseAdapter, ValidationError
from init_postgres_db import create_database


class PostgreSQLAdapter(BaseDatabaseAdapter):
    """PostgreSQL-backed adapter with the same MCP tool surface as SQLite."""

    backend_name = "postgresql"

    def __init__(self, connection_url: str, bootstrap: bool = True) -> None:
        self.connection_url = connection_url
        if bootstrap:
            create_database(connection_url)

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(self.connection_url, row_factory=dict_row)

    def database_label(self) -> str:
        return self.connection_url

    def _placeholder(self) -> str:
        return "%s"

    def list_tables(self) -> list[str]:
        rows = self._fetchall(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            [],
        )
        return [row["table_name"] for row in rows]

    def _get_table_schema_impl(self, table: str) -> dict[str, Any]:
        columns = self._fetchall(
            """
            SELECT
                c.column_name AS name,
                c.data_type AS type,
                CASE WHEN c.is_nullable = 'NO' THEN true ELSE false END AS not_null,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END AS primary_key,
                c.column_default AS default
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_schema = 'public'
                  AND tc.table_name = %s
            ) pk ON pk.column_name = c.column_name
            WHERE c.table_schema = 'public'
              AND c.table_name = %s
            ORDER BY c.ordinal_position
            """,
            [table, table],
        )

        foreign_keys = self._fetchall(
            """
            SELECT
                kcu.column_name AS column,
                ccu.table_name AS references_table,
                ccu.column_name AS references_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = %s
            ORDER BY kcu.ordinal_position
            """,
            [table],
        )

        return {
            "table": table,
            "columns": columns,
            "foreign_keys": foreign_keys,
        }

    def _execute_insert_and_fetch(
        self,
        table: str,
        columns: list[str],
        params: list[Any],
    ) -> dict[str, Any]:
        column_sql = ", ".join(columns)
        placeholders = self._placeholders(len(columns))
        query = (
            f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) "
            f"RETURNING *"
        )

        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
            conn.commit()

        if row is None:
            raise ValidationError("insert did not return a row")
        return dict(row)

    def _fetchall(self, query: str, params: list[Any]) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def _fetchone(self, query: str, params: list[Any]) -> dict[str, Any]:
        rows = self._fetchall(query, params)
        if not rows:
            raise ValidationError("query returned no rows")
        return rows[0]
