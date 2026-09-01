# A3 — Your First Background Job

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