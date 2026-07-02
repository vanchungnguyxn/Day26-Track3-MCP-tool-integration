"""FastMCP server exposing SQLite/PostgreSQL search, insert, aggregate tools and schema resources."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from fastmcp import FastMCP

from adapter_factory import create_adapter
from base_db import BaseDatabaseAdapter, ValidationError

adapter: BaseDatabaseAdapter = create_adapter()


def build_auth():
    """Bearer-token auth for HTTP/SSE transports (bonus feature)."""
    api_key = os.getenv("MCP_API_KEY")
    if not api_key:
        return None

    from fastmcp.server.auth import StaticTokenVerifier

    return StaticTokenVerifier(
        tokens={
            api_key: {
                "client_id": "sqlite-lab-client",
                "scopes": ["mcp:access"],
            }
        },
        required_scopes=["mcp:access"],
    )


def create_server() -> FastMCP:
    auth = build_auth()
    return FastMCP(
        "SQLite Lab MCP Server",
        instructions=(
            "Use this server to inspect the database schema and run safe database operations. "
            "Tools: search (query rows), insert (add rows), aggregate (count/avg/sum/min/max). "
            "Resources: schema://database and schema://table/{table_name}."
        ),
        auth=auth,
    )


mcp = create_server()


def _error(message: str) -> dict[str, Any]:
    return {"error": message}


@mcp.tool(
    name="search",
    description=(
        "Search rows from a table with optional filters, column selection, ordering, "
        "and pagination. Filters use objects with column, operator, and value."
    ),
)
def search(
    table: str,
    filters: list[dict[str, Any]] | None = None,
    columns: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
) -> dict[str, Any]:
    """Search database rows."""
    try:
        return adapter.search(
            table=table,
            columns=columns,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
        )
    except ValidationError as exc:
        return _error(str(exc))


@mcp.tool(
    name="insert",
    description="Insert a new row into a table and return the inserted record.",
)
def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
    """Insert a row into a table."""
    try:
        return adapter.insert(table=table, values=values)
    except ValidationError as exc:
        return _error(str(exc))


@mcp.tool(
    name="aggregate",
    description=(
        "Run aggregate metrics on a table. Supported metrics: count, avg, sum, min, max. "
        "Use group_by for grouped aggregates."
    ),
)
def aggregate(
    table: str,
    metric: str,
    column: str | None = None,
    filters: list[dict[str, Any]] | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """Aggregate table data."""
    try:
        return adapter.aggregate(
            table=table,
            metric=metric,
            column=column,
            filters=filters,
            group_by=group_by,
        )
    except ValidationError as exc:
        return _error(str(exc))


@mcp.resource(
    "schema://database",
    description="Full database schema including all tables, columns, and foreign keys.",
)
def database_schema() -> str:
    """Return the full database schema as JSON."""
    return json.dumps(adapter.get_database_schema(), indent=2)


@mcp.resource(
    "schema://table/{table_name}",
    description="Schema for a single table identified by table_name.",
)
def table_schema(table_name: str) -> str:
    """Return schema for one table as JSON."""
    try:
        schema = adapter.get_table_schema(table_name)
        return json.dumps(schema, indent=2)
    except ValidationError as exc:
        return json.dumps({"error": str(exc)}, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SQLite Lab MCP Server")
    parser.add_argument(
        "--transport",
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        choices=["stdio", "sse", "http", "streamable-http"],
        help="MCP transport (default: stdio, or MCP_TRANSPORT env)",
    )
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8000")))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.transport == "stdio" and sys.stdin.isatty():
        print(
            "\n"
            "NOTE: This process speaks the MCP JSON-RPC protocol on stdin/stdout.\n"
            "Do NOT paste tool JSON here — that will cause validation errors.\n"
            "\n"
            "To test tools from this terminal instead, open a new window and run:\n"
            "  python demo_tools.py\n"
            "  python verify_server.py\n"
            "\n"
            "For a GUI, run: .\\start_inspector.bat\n"
            "For HTTP/SSE with auth (bonus): set MCP_API_KEY then run\n"
            "  python mcp_server.py --transport sse --port 8000\n"
            "\n"
            "Waiting for an MCP client to connect...\n",
            file=sys.stderr,
        )

    if args.transport in {"sse", "http", "streamable-http"} and not os.getenv("MCP_API_KEY"):
        print(
            "WARNING: HTTP/SSE transport is running without MCP_API_KEY.\n"
            "Set MCP_API_KEY for bearer-token auth before exposing this server.\n",
            file=sys.stderr,
        )

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
