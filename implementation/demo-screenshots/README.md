# MCP Inspector Demo Screenshots

Screenshots from testing **SQLite Lab MCP Server** with MCP Inspector v0.22.0.

## Files

| File | Mô tả |
|------|--------|
| [01-search-cohort-a1.png](01-search-cohort-a1.png) | Tool `search` — lọc cohort A1, sort theo `score` giảm dần, `limit: 5` |
| [02-insert-student.png](02-insert-student.png) | Tool `insert` — thêm sinh viên Frank Vo, trả về `id: 9` |
| [03-aggregate-avg-by-cohort.png](03-aggregate-avg-by-cohort.png) | Tool `aggregate` — `avg(score)` group by `cohort` |
| [04-resource-schema-database.png](04-resource-schema-database.png) | Resource `schema://database` — full schema (students, courses, enrollments) |
| [05-error-unknown-table.png](05-error-unknown-table.png) | Error handling — `table: missing_table` → `unknown table` |

## Rubric coverage

- Server starts and connects via stdio
- Tools discoverable: `search`, `insert`, `aggregate`
- Schema resource discoverable and readable
- Valid tool calls return useful results
- Invalid requests return clear errors

## How to reproduce

```powershell
cd implementation
.\start_inspector.bat
```

Then connect in the browser and run the same tool calls as shown in the screenshots.
