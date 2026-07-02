"""Run example MCP tool calls from the terminal (no Inspector required)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client

SERVER_PATH = Path(__file__).resolve().parent / "mcp_server.py"


def _pretty(data: object) -> str:
    if isinstance(data, (dict, list)):
        return json.dumps(data, indent=2, ensure_ascii=False)
    return str(data)


def _tool_payload(result: object) -> object:
    if hasattr(result, "data"):
        return result.data
    if hasattr(result, "content") and result.content:
        texts = [getattr(block, "text", "") for block in result.content]
        combined = "\n".join(text for text in texts if text)
        try:
            return json.loads(combined)
        except json.JSONDecodeError:
            return combined
    return result


async def run_demo() -> None:
    print("SQLite Lab MCP - Demo Tool Calls")
    print("=" * 40)

    async with Client(SERVER_PATH) as client:
        print("\n[search] Top students in cohort A1")
        search_result = await client.call_tool(
            "search",
            {
                "table": "students",
                "filters": [{"column": "cohort", "operator": "eq", "value": "A1"}],
                "order_by": "score",
                "descending": True,
                "limit": 3,
            },
        )
        print(_pretty(_tool_payload(search_result)))

        print("\n[insert] Add a demo student")
        insert_result = await client.call_tool(
            "insert",
            {
                "table": "students",
                "values": {"name": "Demo Student", "cohort": "A1", "score": 87.5},
            },
        )
        print(_pretty(_tool_payload(insert_result)))

        print("\n[aggregate] Average score by cohort")
        aggregate_result = await client.call_tool(
            "aggregate",
            {
                "table": "students",
                "metric": "avg",
                "column": "score",
                "group_by": "cohort",
            },
        )
        print(_pretty(_tool_payload(aggregate_result)))

        print("\n[resource] schema://table/students")
        table_schema = await client.read_resource("schema://table/students")
        text = table_schema[0].text if isinstance(table_schema, list) else table_schema.text
        print(text)

        print("\n[error demo] Unknown table")
        invalid_result = await client.call_tool("search", {"table": "missing_table"})
        print(_pretty(_tool_payload(invalid_result)))

    print("\nDemo complete.")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        sys.exit(130)
