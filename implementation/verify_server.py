"""Repeatable verification script for the SQLite Lab MCP server."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastmcp import Client

SERVER_PATH = Path(__file__).resolve().parent / "mcp_server.py"

REQUIRED_TOOLS = {"search", "insert", "aggregate"}
REQUIRED_RESOURCES = {"schema://database"}


async def verify() -> int:
    print("SQLite Lab MCP Server Verification")
    print("=" * 40)

    async with Client(SERVER_PATH) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        print(f"\n[1] Tool discovery: {sorted(tool_names)}")
        missing_tools = REQUIRED_TOOLS - tool_names
        if missing_tools:
            print(f"    FAIL - missing tools: {sorted(missing_tools)}")
            return 1
        print("    PASS")

        resources = await client.list_resources()
        resource_uris = {str(resource.uri) for resource in resources}
        print(f"\n[2] Resource discovery: {sorted(resource_uris)}")
        if not any(uri.startswith("schema://") for uri in resource_uris):
            print("    FAIL - schema resource not found")
            return 1
        print("    PASS")

        print("\n[3] Valid search call")
        search_result = await client.call_tool(
            "search",
            {
                "table": "students",
                "filters": [{"column": "cohort", "operator": "eq", "value": "A1"}],
                "order_by": "score",
                "descending": True,
                "limit": 2,
            },
        )
        search_text = _tool_text(search_result)
        print(f"    Result preview: {search_text[:200]}...")
        if "error" in search_text.lower() and "Alice" not in search_text:
            print("    FAIL")
            return 1
        print("    PASS")

        print("\n[4] Valid insert call")
        insert_result = await client.call_tool(
            "insert",
            {
                "table": "students",
                "values": {
                    "name": "Verify Student",
                    "cohort": "A1",
                    "score": 99.5,
                },
            },
        )
        insert_text = _tool_text(insert_result)
        print(f"    Result preview: {insert_text[:200]}...")
        if "Verify Student" not in insert_text:
            print("    FAIL")
            return 1
        print("    PASS")

        print("\n[5] Valid aggregate call")
        aggregate_result = await client.call_tool(
            "aggregate",
            {
                "table": "students",
                "metric": "avg",
                "column": "score",
                "group_by": "cohort",
            },
        )
        aggregate_text = _tool_text(aggregate_result)
        print(f"    Result preview: {aggregate_text[:200]}...")
        if "value" not in aggregate_text:
            print("    FAIL")
            return 1
        print("    PASS")

        print("\n[6] Invalid table search")
        invalid_result = await client.call_tool(
            "search",
            {"table": "missing_table"},
        )
        invalid_text = _tool_text(invalid_result)
        print(f"    Result: {invalid_text[:200]}")
        if "unknown table" not in invalid_text.lower():
            print("    FAIL - expected clear validation error")
            return 1
        print("    PASS")

        print("\n[7] Database schema resource")
        schema_result = await client.read_resource("schema://database")
        schema_text = _resource_text(schema_result)
        print(f"    Result preview: {schema_text[:200]}...")
        if "students" not in schema_text:
            print("    FAIL")
            return 1
        print("    PASS")

        print("\n[8] Table schema resource template")
        table_schema_result = await client.read_resource("schema://table/students")
        table_schema_text = _resource_text(table_schema_result)
        print(f"    Result preview: {table_schema_text[:200]}...")
        if "cohort" not in table_schema_text:
            print("    FAIL")
            return 1
        print("    PASS")

    print("\nAll verification checks passed.")
    return 0


def _tool_text(result: object) -> str:
    if hasattr(result, "data"):
        data = result.data
        if isinstance(data, dict):
            return str(data)
        return str(data)
    if hasattr(result, "content") and result.content:
        parts = []
        for block in result.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts)
    return str(result)


def _resource_text(result: object) -> str:
    if isinstance(result, list) and result:
        first = result[0]
        if hasattr(first, "text"):
            return first.text
    if hasattr(result, "text"):
        return result.text
    return str(result)


if __name__ == "__main__":
    sys.exit(asyncio.run(verify()))
