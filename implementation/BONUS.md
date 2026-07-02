# Bonus Features

Optional lab bonus: up to **+10 points**.

## Implemented bonus

### 1. SSE / HTTP bearer auth (+5)

The server supports remote transports with a static bearer token.

**Start SSE server with auth:**

```powershell
set MCP_API_KEY=sqlite-lab-dev-token
.\start_sse_server.bat
```

Or manually:

```powershell
$env:MCP_API_KEY="sqlite-lab-dev-token"
python mcp_server.py --transport sse --host 127.0.0.1 --port 8000
```

**Verify auth:**

```powershell
python verify_sse_auth.py
```

Checks:

- missing bearer token is rejected
- valid `Authorization: Bearer <MCP_API_KEY>` can reach `/sse`
- FastMCP client can list tools over authenticated SSE

Supported transports: `stdio` (default), `sse`, `http`, `streamable-http`.

Environment variables:

| Variable | Purpose |
|----------|---------|
| `MCP_API_KEY` | Bearer token for HTTP/SSE auth |
| `MCP_TRANSPORT` | Default transport when using env-driven startup |
| `MCP_HOST` | Bind host for HTTP/SSE |
| `MCP_PORT` | Bind port for HTTP/SSE |

### 2. SQLite + PostgreSQL shared interface (+3)

Database access is split into:

- `base_db.py` — shared validation and query surface
- `db.py` — `SQLiteAdapter`
- `postgres_db.py` — `PostgreSQLAdapter`
- `adapter_factory.py` — selects backend from env

**SQLite (default):**

```powershell
python init_db.py
python verify_server.py
```

**PostgreSQL:**

```powershell
$env:DB_BACKEND="postgresql"
$env:DATABASE_URL="postgresql://user:pass@localhost:5432/sqlite_lab"
python init_postgres_db.py
python verify_server.py
```

Both backends expose the same MCP tools and resources:

- `search`
- `insert`
- `aggregate`
- `schema://database`
- `schema://table/{table_name}`

### 3. Extra polish (+2)

Already included:

- pagination metadata in `search`
- `verify_server.py`, `verify_sse_auth.py`
- `demo_tools.py`
- `demo-screenshots/`
- pytest suite with `run_tests.bat`

## Expected bonus score

| Item | Points | Status |
|------|--------|--------|
| SSE/HTTP auth | +5 | Implemented + `verify_sse_auth.py` |
| SQLite + PostgreSQL | +3 | Implemented via shared adapter interface |
| Extra polish | +2 | Implemented |

**Potential bonus total: +10**

## Notes

- `StaticTokenVerifier` is for local demos only; do not use plain-text API keys in production.
- PostgreSQL tests are skipped automatically unless `DATABASE_URL` is set.
- Stdio transport remains the recommended default for classroom MCP clients.
