"""Shared database types, validation, and query-building base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

SUPPORTED_OPERATORS = frozenset({"eq", "ne", "gt", "gte", "lt", "lte", "like", "in"})

OPERATOR_SQL = {
    "eq": "=",
    "ne": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "like": "LIKE",
    "in": "IN",
}

SUPPORTED_METRICS = frozenset({"count", "avg", "sum", "min", "max"})

METRIC_SQL = {
    "count": "COUNT",
    "avg": "AVG",
    "sum": "SUM",
    "min": "MIN",
    "max": "MAX",
}


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


class BaseDatabaseAdapter(ABC):
    """Shared MCP database surface with backend-specific connection hooks."""

    backend_name: str = "unknown"

    @abstractmethod
    def connect(self) -> Any:
        """Return a DB connection or context-managed connection factory."""

    @abstractmethod
    def list_tables(self) -> list[str]:
        """Return user-facing table names."""

    @abstractmethod
    def _get_table_schema_impl(self, table: str) -> dict[str, Any]:
        """Return column and foreign-key metadata for one table."""

    @abstractmethod
    def database_label(self) -> str:
        """Human-readable database identifier for schema resources."""

    @abstractmethod
    def _placeholder(self) -> str:
        """Return the parameter placeholder for this backend ('?' or '%s')."""

    @abstractmethod
    def _execute_insert_and_fetch(
        self,
        table: str,
        columns: list[str],
        params: list[Any],
    ) -> dict[str, Any]:
        """Insert one row and return the inserted record."""

    def _placeholders(self, count: int) -> str:
        token = self._placeholder()
        return ", ".join(token for _ in range(count))

    def get_table_schema(self, table: str) -> dict[str, Any]:
        table = self._validate_table(table)
        return self._get_table_schema_impl(table)

    def get_database_schema(self) -> dict[str, Any]:
        tables = self.list_tables()
        return {
            "backend": self.backend_name,
            "database": self.database_label(),
            "tables": [self.get_table_schema(table) for table in tables],
        }

    def search(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: list[dict[str, Any]] | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        table = self._validate_table(table)
        selected_columns = self._validate_columns(table, columns)
        where_sql, params = self._build_filters(table, filters)

        if limit < 0 or offset < 0:
            raise ValidationError("limit and offset must be non-negative integers")

        order_sql = ""
        if order_by is not None:
            order_column = self._validate_column(table, order_by)
            direction = "DESC" if descending else "ASC"
            order_sql = f" ORDER BY {order_column} {direction}"

        column_sql = ", ".join(selected_columns)
        limit_sql = f" LIMIT {self._placeholder()} OFFSET {self._placeholder()}"
        query = f"SELECT {column_sql} FROM {table}{where_sql}{order_sql}{limit_sql}"
        query_params = [*params, limit, offset]

        rows = self._fetchall(query, query_params)
        total = self._fetchone(
            f"SELECT COUNT(*) AS total FROM {table}{where_sql}",
            params,
        )["total"]

        return {
            "table": table,
            "rows": rows,
            "count": len(rows),
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        table = self._validate_table(table)

        if not values:
            raise ValidationError("insert values cannot be empty")

        columns = self._validate_columns(table, list(values.keys()))
        params = [values[col] for col in columns]
        inserted = self._execute_insert_and_fetch(table, columns, params)

        return {"table": table, "inserted": inserted}

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: list[dict[str, Any]] | None = None,
        group_by: str | None = None,
    ) -> dict[str, Any]:
        table = self._validate_table(table)
        metric = metric.lower().strip()

        if metric not in SUPPORTED_METRICS:
            raise ValidationError(
                f"unsupported metric '{metric}'. Supported metrics: {sorted(SUPPORTED_METRICS)}"
            )

        if metric == "count" and column is None:
            aggregate_expr = "COUNT(*)"
        else:
            if column is None:
                raise ValidationError(f"metric '{metric}' requires a column")
            validated_column = self._validate_column(table, column)
            aggregate_expr = f"{METRIC_SQL[metric]}({validated_column})"

        where_sql, params = self._build_filters(table, filters)

        select_parts: list[str] = []
        group_sql = ""
        if group_by is not None:
            group_column = self._validate_column(table, group_by)
            select_parts.append(group_column)
            group_sql = f" GROUP BY {group_column}"

        select_parts.append(f"{aggregate_expr} AS value")
        query = f"SELECT {', '.join(select_parts)} FROM {table}{where_sql}{group_sql}"
        rows = self._fetchall(query, params)

        results = []
        for row in rows:
            item: dict[str, Any] = {"value": row["value"]}
            if group_by is not None:
                item[group_by] = row[group_by]
            results.append(item)

        return {
            "table": table,
            "metric": metric,
            "column": column,
            "group_by": group_by,
            "results": results,
        }

    def _fetchall(self, query: str, params: list[Any]) -> list[dict[str, Any]]:
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def _fetchone(self, query: str, params: list[Any]) -> dict[str, Any]:
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            if row is None:
                raise ValidationError("query returned no rows")
            return dict(row)

    def _validate_table(self, table: str) -> str:
        if not isinstance(table, str) or not table.strip():
            raise ValidationError("table name is required")

        table = table.strip()
        if table not in self.list_tables():
            raise ValidationError(f"unknown table '{table}'")
        return table

    def _validate_column(self, table: str, column: str) -> str:
        if not isinstance(column, str) or not column.strip():
            raise ValidationError("column name is required")

        column = column.strip()
        schema = self.get_table_schema(table)
        valid_names = {col["name"] for col in schema["columns"]}
        if column not in valid_names:
            raise ValidationError(f"unknown column '{column}' in table '{table}'")
        return column

    def _validate_columns(self, table: str, columns: list[str] | None) -> list[str]:
        if columns is None:
            schema = self.get_table_schema(table)
            return [col["name"] for col in schema["columns"]]

        if not columns:
            raise ValidationError("columns list cannot be empty when provided")

        return [self._validate_column(table, column) for column in columns]

    def _build_filters(
        self,
        table: str,
        filters: list[dict[str, Any]] | None,
    ) -> tuple[str, list[Any]]:
        if not filters:
            return "", []

        clauses: list[str] = []
        params: list[Any] = []

        for index, raw_filter in enumerate(filters):
            if not isinstance(raw_filter, dict):
                raise ValidationError(f"filter at index {index} must be an object")

            column = raw_filter.get("column")
            operator = str(raw_filter.get("operator", "eq")).lower().strip()
            value = raw_filter.get("value")

            if column is None:
                raise ValidationError(f"filter at index {index} is missing 'column'")

            validated_column = self._validate_column(table, str(column))

            if operator not in SUPPORTED_OPERATORS:
                raise ValidationError(
                    f"unsupported operator '{operator}'. "
                    f"Supported operators: {sorted(SUPPORTED_OPERATORS)}"
                )

            placeholder = self._placeholder()
            if operator == "in":
                if not isinstance(value, list) or not value:
                    raise ValidationError(
                        f"operator 'in' requires a non-empty list value for column '{column}'"
                    )
                placeholders = ", ".join(placeholder for _ in value)
                clauses.append(f"{validated_column} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{validated_column} {OPERATOR_SQL[operator]} {placeholder}")
                params.append(value)

        return " WHERE " + " AND ".join(clauses), params
