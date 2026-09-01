# A3 ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â Your First Background Job

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
## Stage 1 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Inngest connected

The API now exposes the Inngest serve endpoint at `/api/inngest` and registers one function:

| Function | Trigger | Durable step | Result |
|---|---|---|---|
| `say-hello` | event `test/hello` | sleep 5 seconds | `Hello from the background!` |

Run the two programs in separate terminals.

### Terminal 1 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â FastAPI

```powershell
cd C:\Users\haide\task-api\background-job
$env:INNGEST_DEV="1"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

### Terminal 2 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Inngest Dev Server

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
## Stage 2 Ã¢â‚¬â€ Accept fast, work later

`POST /reports` accepts a topic, stores a `pending` report, sends the `report/requested` event, and returns HTTP `202 Accepted` immediately.

The `make-report` Inngest function performs two durable steps:
1. `do-the-slow-work` Ã¢â‚¬â€ 8-second sleep
2. `build-report` Ã¢â‚¬â€ saves the result and changes the report to `done`

Use `GET /reports/{id}` to poll status. The first poll returns `pending`; after the background function completes, the same endpoint returns `done` plus the result. Unknown IDs return `404`.
## Stage 3 â€” Retries and bad-input rejection

The `make-report` function is configured with `retries=2`. A report whose topic is exactly `fail` raises `The report oven is broken!` inside the `build-report` step. Inngest therefore makes three total attempts: the initial attempt plus two retries, using backoff between attempts.

A request with a missing, blank, or non-string `topic` is rejected with HTTP `400` before `inngest_client.send(...)` is reached, so no background job is created.

**Why the difference:** invalid input is rejected at the request boundary because retrying bad data cannot make it valid; retries are for work that started with valid input but failed because execution can fail temporarily.
## Stage 4 — Cron heartbeat

The `heartbeat` Inngest function is triggered only by this cron schedule:

```text
* * * * *
```

That means **every minute**. Each run logs one summary line with the current number of `pending`, `done`, and `failed` reports.

The clock is the only trigger: there is no request endpoint and no event that starts `heartbeat`.

Cron answers required by the assignment:

- Every day at 08:00: `0 8 * * *`
- Every Sunday at 22:00: `0 22 * * 0`

Cron schedules normally run in the scheduler/server timezone unless an explicit timezone is configured, so production schedules should always have their timezone checked.