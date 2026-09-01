# PDF Report Generator

FlyRank Internship — Backend Track — Assignment A8.

This assignment builds a synchronous data-to-document pipeline:

```text
SQLite data -> SQL aggregation -> HTML -> PDF -> file link
```

The Python lane uses FastAPI, Python's built-in `sqlite3`, and Playwright with headless Chromium.

The project uses the bookstore dataset option: 60 validated book records are seeded into a local SQLite database in Stage 1.

## Stage 0

Stage 0 provides:

- `GET /health`
- FastAPI on port 8000
- Playwright installed
- Chromium installed for PDF rendering

Run the API from this folder:

```powershell
$env:PYTHONUTF8="1"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Health check:

```powershell
curl.exe -i http://localhost:8000/health
```

Expected body:

```json
{"status":"ok"}
```

Later stages add SQLite seeding, aggregation queries, HTML-to-PDF rendering, report records, download links, and once-per-day idempotency.