# A3 Ã¢â‚¬â€ Your First Background Job

This folder contains the FlyRank backend assignment for building a FastAPI service whose slow work will later run through Inngest.

## Stage 0

Stage 0 provides the normal API that the background-job system will grow from.

### Run

From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Then verify:

```powershell
curl.exe -i http://localhost:8000/health
```

Expected JSON:

```json
{"status":"ok"}
```

Later stages will add Inngest, `POST /reports`, the background worker, retry behavior, a status endpoint, and a cron heartbeat.
## Stage 1 â€” Inngest connected

The API now exposes the Inngest serve endpoint at `/api/inngest` and registers one function:

| Function | Trigger | Durable step | Result |
|---|---|---|---|
| `say-hello` | event `test/hello` | sleep 5 seconds | `Hello from the background!` |

Run the two programs in separate terminals.

### Terminal 1 â€” FastAPI

```powershell
cd C:\Users\haide\task-api\background-job
$env:INNGEST_DEV="1"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

### Terminal 2 â€” Inngest Dev Server

```powershell
cd C:\Users\haide\task-api\background-job
npx --ignore-scripts=false inngest-cli@latest dev --no-discovery -u http://localhost:8000/api/inngest
```

Open the dashboard:

```text
http://localhost:8288
```

Local test event:

```powershell
curl.exe -X POST http://localhost:8288/e/test-key `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"test/hello\",\"data\":{\"source\":\"manual-test\"}}"
```

The resulting `say-hello` run should show the `wait-five-seconds` sleep step and finish **Completed** with:

```text
Hello from the background!
```