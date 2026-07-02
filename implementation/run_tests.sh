#!/usr/bin/env bash
set -euo pipefail
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python -m pytest tests/ -v -p pytest_asyncio.plugin "$@"
