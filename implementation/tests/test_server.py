"""Automated tests for the SQLite Lab MCP server."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from base_db import ValidationError
from db import SQLiteAdapter
from init_db import create_database


@pytest.fixture()
def adapter(tmp_path: Path) -> SQLiteAdapter:
    db_path = tmp_path / "test.db"
    create_database(db_path, force=True)
    return SQLiteAdapter(db_path)


def test_list_tables(adapter: SQLiteAdapter) -> None:
    tables = adapter.list_tables()
    assert tables == ["courses", "enrollments", "students"]


def test_search_with_filters_and_pagination(adapter: SQLiteAdapter) -> None:
    result = adapter.search(
        table="students",
        filters=[{"column": "cohort", "operator": "eq", "value": "A1"}],
        order_by="score",
        descending=True,
        limit=2,
        offset=0,
    )
    assert result["count"] == 2
    assert result["rows"][0]["name"] == "Alice Nguyen"


def test_insert_returns_row(adapter: SQLiteAdapter) -> None:
    result = adapter.insert(
        table="students",
        values={"name": "Test User", "cohort": "B2", "score": 70.0},
    )
    assert result["inserted"]["name"] == "Test User"
    assert result["inserted"]["id"] is not None


def test_aggregate_count_and_group_by(adapter: SQLiteAdapter) -> None:
    count_result = adapter.aggregate(table="students", metric="count")
    assert count_result["results"][0]["value"] == 5

    avg_result = adapter.aggregate(
        table="students",
        metric="avg",
        column="score",
        group_by="cohort",
    )
    cohorts = {row["cohort"] for row in avg_result["results"]}
    assert cohorts == {"A1", "B2"}


def test_rejects_unknown_table(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="unknown table"):
        adapter.search(table="ghost_table")


def test_rejects_unknown_column(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="unknown column"):
        adapter.search(
            table="students",
            filters=[{"column": "missing", "operator": "eq", "value": 1}],
        )


def test_rejects_unsupported_operator(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="unsupported operator"):
        adapter.search(
            table="students",
            filters=[{"column": "cohort", "operator": "regex", "value": "A1"}],
        )


def test_rejects_empty_insert(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="cannot be empty"):
        adapter.insert(table="students", values={})


def test_rejects_invalid_metric(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="unsupported metric"):
        adapter.aggregate(table="students", metric="median", column="score")


def test_database_schema_resource(adapter: SQLiteAdapter) -> None:
    schema = adapter.get_database_schema()
    table_names = [table["table"] for table in schema["tables"]]
    assert "students" in table_names
    assert "courses" in table_names


def test_table_schema_resource(adapter: SQLiteAdapter) -> None:
    schema = adapter.get_table_schema("students")
    column_names = [column["name"] for column in schema["columns"]]
    assert column_names == ["id", "name", "cohort", "score"]


def test_adapter_factory_defaults_to_sqlite() -> None:
    import os

    old_backend = os.environ.get("DB_BACKEND")
    os.environ.pop("DB_BACKEND", None)
    try:
        from adapter_factory import create_adapter

        created = create_adapter()
        assert created.backend_name == "sqlite"
    finally:
        if old_backend is not None:
            os.environ["DB_BACKEND"] = old_backend


@pytest.mark.asyncio
async def test_mcp_client_integration() -> None:
    from fastmcp import Client

    server_path = Path(__file__).resolve().parent.parent / "mcp_server.py"
    async with Client(server_path) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        assert {"search", "insert", "aggregate"}.issubset(tool_names)

        schema = await client.read_resource("schema://database")
        schema_text = schema[0].text if isinstance(schema, list) else schema.text
        payload = json.loads(schema_text)
        assert any(table["table"] == "students" for table in payload["tables"])
