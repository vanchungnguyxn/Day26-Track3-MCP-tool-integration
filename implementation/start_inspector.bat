@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PYTHON_BIN=python"
rem Forward slashes avoid backslash-escape issues when npx passes args to Inspector.
set "SERVER_PATH=%SCRIPT_DIR%mcp_server.py"
set "SERVER_PATH=%SERVER_PATH:\=/%"
set "CACHE_DIR=%SCRIPT_DIR%.npm-cache"

if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
set "NPM_CONFIG_CACHE=%CACHE_DIR%"

echo Starting MCP Inspector...
echo Server: %SERVER_PATH%
echo.
echo Open the browser URL shown below, then:
echo   1. Connect (Transport: STDIO should already be filled in)
echo   2. Open the Tools tab - try search / insert / aggregate
echo   3. Open the Resources tab - read schema://database
echo.
echo Press Ctrl+C here to stop Inspector.
echo.

npx -y @modelcontextprotocol/inspector "%PYTHON_BIN%" "%SERVER_PATH%"
