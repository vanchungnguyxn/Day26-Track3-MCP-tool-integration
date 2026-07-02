#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
SERVER_PATH="${SCRIPT_DIR}/mcp_server.py"
CACHE_DIR="${SCRIPT_DIR}/.npm-cache"

mkdir -p "${CACHE_DIR}"
NPM_CONFIG_CACHE="${CACHE_DIR}" npx -y @modelcontextprotocol/inspector "${PYTHON_BIN}" "${SERVER_PATH}"
