"""Verify SSE transport with bearer-token auth (bonus feature)."""
""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

SERVER_PATH = Path(__file__).resolve().parent / "mcp_server.py"
API_KEY = os.getenv("MCP_API_KEY", "sqlite-lab-dev-token")
HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "8765"))
BASE_URL = f"http://{HOST}:{PORT}"
SSE_URL = f"{BASE_URL}/sse"


async def verify() -> int:
    print("SSE + Bearer Auth Verification")
    print("=" * 40)

    env = os.environ.copy()
    env["MCP_API_KEY"] = API_KEY

    process = subprocess.Popen(
        [
            sys.executable,
            str(SERVER_PATH),
            "--transport",
            "sse",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    try:
        await _wait_for_server()
        print("\n[1] Unauthenticated request should be rejected")
        async with httpx.AsyncClient(follow_redirects=False) as client:
            response = await client.get(SSE_URL, timeout=5.0)
        print(f"    Status without token: {response.status_code}")
        if response.status_code not in {401, 403}:
            print("    FAIL - expected 401/403 for missing bearer token")
            return 1
        print("    PASS")

        print("\n[2] Authenticated SSE endpoint reachable")
        async with httpx.AsyncClient(follow_redirects=False) as client:
            async with client.stream(
                "GET",
                SSE_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=5.0,
            ) as response:
                status = response.status_code
        print(f"    Status with token: {status}")
        if status not in {200, 307}:
            print("    FAIL")
            return 1
        print("    PASS")

        print("\n[3] FastMCP client can connect with bearer auth")
        from fastmcp import Client
        from fastmcp.client.transports import SSETransport

        transport = SSETransport(url=SSE_URL, auth=API_KEY)
        async with Client(transport) as client:
            tools = await client.list_tools()
            tool_names = {tool.name for tool in tools}
            print(f"    Tools: {sorted(tool_names)}")
            if not {"search", "insert", "aggregate"}.issubset(tool_names):
                print("    FAIL")
                return 1
        print("    PASS")

        print("\nAll SSE auth checks passed.")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


async def _wait_for_server() -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(HOST, PORT),
                timeout=1.0,
            )
            writer.close()
            await writer.wait_closed()
            await asyncio.sleep(1.0)
            return
        except (TimeoutError, OSError, ConnectionError):
            await asyncio.sleep(0.5)
    raise RuntimeError("SSE server did not become ready in time")


if __name__ == "__main__":
    sys.exit(asyncio.run(verify()))
