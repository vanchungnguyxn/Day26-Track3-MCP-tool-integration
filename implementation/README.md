# SQLite Lab MCP Server - Implementation

FastMCP server exposing a SQLite database through `search`, `insert`, and `aggregate` tools, plus schema resources.

## Project Structure

```text
implementation/
  db.py                 # SQLite adapter and validation
  init_db.py            # Schema + seed data
  mcp_server.py         # FastMCP server entrypoint
  verify_server.py      # Repeatable verification script
  demo_tools.py         # Run example tool calls from terminal
  tests/
    test_server.py      # Automated tests
  requirements.txt
  .mcp.json             # Claude Code client example
  start_inspector.sh    # MCP Inspector helper (Linux/macOS)
  start_inspector.bat   # MCP Inspector helper (Windows)
  demo-screenshots/     # Inspector screenshots for demo submission
```

## Setup

```bash
cd implementation
pip install -r requirements.txt
python init_db.py
```

This creates `lab.db` with three tables:

- `students` - student name, cohort, score
- `courses` - course title and instructor
- `enrollments` - student/course enrollments with grades

## Run the Server

```bash
python mcp_server.py
```

The server uses **stdio transport**. It waits for an MCP client over stdin/stdout using the JSON-RPC protocol.

**Important:** Do not paste tool JSON directly into this terminal. Raw JSON like `{"table": "students", ...}` is not valid MCP input and will cause validation errors.

Use one of these instead:

| Goal | Command |
|------|---------|
| Quick demo from terminal | `python demo_tools.py` |
| Full automated checks | `python verify_server.py` |
| Interactive UI | `.\start_inspector.bat` (Windows) |
| Connect from AI client | Claude Code / Gemini CLI / Codex |

When `python mcp_server.py` is running correctly, the terminal looks idle. That is normal. Connect an MCP client in another terminal or through Inspector.

## Tools

### `search`

Query rows with filters, ordering, and pagination.

Supported filter operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `in`.

```json
{
  "table": "students",
  "filters": [{"column": "cohort", "operator": "eq", "value": "A1"}],
  "order_by": "score",
  "descending": true,
  "limit": 10,
  "offset": 0
}
```

### `insert`

Insert one row and return the inserted record.

```json
{
  "table": "students",
  "values": {"name": "Frank Vo", "cohort": "A1", "score": 91.0}
}
```

### `aggregate`

Run `count`, `avg`, `sum`, `min`, or `max`.

```json
{
  "table": "students",
  "metric": "avg",
  "column": "score",
  "group_by": "cohort"
}
```

## Resources

- `schema://database` - full database schema
- `schema://table/{table_name}` - schema for one table, e.g. `schema://table/students`

## Verification

### Automated tests

Windows PowerShell:

```powershell
.\run_tests.bat
```

Windows CMD:

```bat
run_tests.bat
```

Linux/macOS:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

If global pytest plugins cause conflicts on your machine, the helper scripts disable autoload and enable only `pytest-asyncio`.

### Verification script

```bash
python verify_server.py
```

### Terminal demo (no Inspector)

```bash
python demo_tools.py
```

This runs example `search`, `insert`, `aggregate`, schema read, and one invalid request.

`verify_server.py` checks:

1. tool discovery
2. resource discovery
3. valid `search`, `insert`, and `aggregate` calls
4. invalid request handling
5. schema resources

## MCP Inspector

Windows:

```powershell
.\start_inspector.bat
```

When the browser opens:

1. Click **Connect** (command should be `python` and args should point to `mcp_server.py`)
2. Open **Tools** → run `search`, `insert`, or `aggregate`
3. Open **Resources** → read `schema://database` or `schema://table/students`
4. Try an invalid table name and confirm you get a clear error

Example `search` arguments in Inspector:

```json
{
  "table": "students",
  "filters": [{"column": "cohort", "operator": "eq", "value": "A1"}],
  "order_by": "score",
  "descending": true,
  "limit": 5
}
```

Press `Ctrl+C` in the terminal to stop Inspector. Answer `Y` if Windows asks `Terminate batch job (Y/N)?`.

Pre-captured Inspector screenshots for submission are in [`demo-screenshots/`](demo-screenshots/).

Client verification evidence for grading: [`CLIENT_VERIFICATION.md`](CLIENT_VERIFICATION.md).  
Optional bonus features (+10): [`BONUS.md`](BONUS.md) — SSE auth + PostgreSQL adapter.

Linux/macOS:

```bash
chmod +x start_inspector.sh
./start_inspector.sh
```

Manual command:

```bash
npx -y @modelcontextprotocol/inspector python mcp_server.py
```

Inspector checklist:

- tools appear with schemas
- resources appear
- valid tool call succeeds
- invalid tool call returns a clear error

## Client Configuration

### Claude Code

Use `.mcp.json` in this folder. Replace paths if your machine differs.

```bash
claude mcp add sqlite-lab -- python E:/VinAI20K/Day26-Track3-MCP-tool-integration/implementation/mcp_server.py
```

Reference schema with:

```text
@sqlite-lab:schema://database
@sqlite-lab:schema://table/students
```

### Gemini CLI

```bash
gemini mcp add sqlite-lab python E:/VinAI20K/Day26-Track3-MCP-tool-integration/implementation/mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
gemini --allowed-mcp-server-names sqlite-lab --yolo -p "Use the sqlite-lab MCP server and show me the top 2 students by score."
```

### Codex

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.sqlite_lab]
command = "python"
args = ["E:/VinAI20K/Day26-Track3-MCP-tool-integration/implementation/mcp_server.py"]
```

## Demo Tasks

1. Search all students in cohort `A1`
2. Insert a new student
3. Count rows in `students`
4. Compute average score by cohort
5. Read `schema://database`
6. Read `schema://table/students`
7. Show invalid request: search table `missing_table`

## Safety Notes

- Table and column names are validated against the live schema
- Unsupported operators and metrics are rejected
- SQL values use parameterized queries
- User input is never concatenated directly into SQL
