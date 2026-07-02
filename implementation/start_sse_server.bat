@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "MCP_API_KEY=%MCP_API_KEY%"
if not defined MCP_API_KEY set "MCP_API_KEY=sqlite-lab-dev-token"

set "MCP_TRANSPORT=sse"
set "MCP_HOST=127.0.0.1"
set "MCP_PORT=8765"

echo Starting SSE MCP server with bearer auth...
echo   URL:   http://%MCP_HOST%:%MCP_PORT%/
echo   Token: %MCP_API_KEY%
echo.
echo Test from another terminal:
echo   python verify_sse_auth.py
echo.

python "%SCRIPT_DIR%mcp_server.py" --transport sse --host %MCP_HOST% --port %MCP_PORT%
