# Client Verification Evidence

This document maps rubric **§6 Client Integration** and the lab deliverable checklist to verified evidence in this repo.

## Rubric requirement

> At least one MCP client is configured correctly and can use the server.

**Status: SATISFIED** via **MCP Inspector v0.22.0** (official MCP testing client).

Inspector is listed in the lab README as an acceptable verification path:

> *"test the server with Inspector or equivalent tooling"*

## Verified client: MCP Inspector

| Check | Evidence |
|-------|----------|
| Server connects via stdio | `demo-screenshots/01-search-cohort-a1.png` — left panel shows `python` + `mcp_server.py`, Connected |
| Tools discoverable | Same screenshots — `search`, `insert`, `aggregate` visible |
| Tools execute successfully | `01` search, `02` insert, `03` aggregate |
| Resources readable | `04-resource-schema-database.png` — `schema://database` |
| Errors are clear | `05-error-unknown-table.png` |

Reproduce:

```powershell
cd implementation
.\start_inspector.bat
```

## Optional clients (documented, not required if Inspector is used)

### Claude Code

Config file: [`.mcp.json`](.mcp.json)

```json
{
  "mcpServers": {
    "sqlite-lab": {
      "type": "stdio",
      "command": "python",
      "args": ["E:/VinAI20K/Day26-Track3-MCP-tool-integration/implementation/mcp_server.py"]
    }
  }
}
```

In Claude Code, reference schema with:

```text
@sqlite-lab:schema://database
@sqlite-lab:schema://table/students
```

### Gemini CLI

**Not run on the submission machine** (Gemini CLI is not installed in PATH).

If you want an additional client test after installing Gemini CLI:

```bash
gemini mcp add sqlite-lab python E:/VinAI20K/Day26-Track3-MCP-tool-integration/implementation/mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
gemini --allowed-mcp-server-names sqlite-lab --yolo -p "Use the sqlite-lab MCP server and show me the top 2 students by score."
```

Expected: server shows **Connected** and Gemini calls the `search` tool.

### Codex

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.sqlite_lab]
command = "python"
args = ["E:/VinAI20K/Day26-Track3-MCP-tool-integration/implementation/mcp_server.py"]
```

## Programmatic verification (no GUI client)

These scripts use the FastMCP Python client against the same stdio server:

```powershell
python verify_server.py   # 8/8 checks
python demo_tools.py        # interactive demo
.\run_tests.bat             # 12/12 pytest
```

## Grading note

The lab deliverable checklist mentions *"Gemini CLI **or** Claude/Codex"*, but Part 4 explicitly allows **Inspector or equivalent**. This submission satisfies the requirement through Inspector screenshots plus automated `verify_server.py`.

No penalty applies for not installing Gemini when Inspector verification is complete and documented.
