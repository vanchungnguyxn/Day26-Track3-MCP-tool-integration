@echo off
setlocal
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python -m pytest tests/ -v -p pytest_asyncio.plugin %*
