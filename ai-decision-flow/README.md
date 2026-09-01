# A1 — AI Decision Flow

A visual AI workflow builder using **Next.js**, **React Flow**, **Inngest**, and the **OpenAI SDK**.

The target workflow is a directed graph of prompt nodes. A node asks the LLM for a strict `YES` or `NO`, then execution follows the corresponding labeled edge to the next node.

## Core assignment targets

- visual React Flow canvas
- add and connect nodes
- edit each node prompt
- YES / NO edge types
- local graph state
- Inngest workflow execution
- one durable Inngest step per graph node
- OpenAI SDK decision call
- strict YES / NO output validation
- execution order tracking
- active-node / active-edge state
- execution logs
- workflow save/load
- JSON import/export
- graceful errors and retries

## Stage 0 — scaffold

The project foundation includes:

- Next.js App Router
- TypeScript
- Tailwind CSS
- React Flow (`@xyflow/react`)
- Inngest SDK
- OpenAI SDK
- Zod
- Lucide icons
- `/api/health`
- `/api/inngest`
- `.env.example` containing variable names only

No API key is committed.

## Run locally

Install dependencies:

```powershell
npm install
```

Start Next.js:

```powershell
npm run dev
```

Open:

```text
http://localhost:3000
```

Health check:

```powershell
curl.exe http://localhost:3000/api/health
```

Expected:

```json
{"status":"ok","app":"ai-decision-flow"}
```

The Inngest serve endpoint is:

```text
http://localhost:3000/api/inngest
```

Later stages register the executable workflow functions.
## Inngest v4 local mode

Inngest v4 defaults to cloud mode. Cloud mode requires a signing key.

For local development this project explicitly uses dev mode:

```env
INNGEST_DEV=1
```

The Inngest client also treats the normal Next.js development environment as dev mode:

```ts
const isDev =
  process.env.INNGEST_DEV === "1" ||
  process.env.NODE_ENV === "development";
```

This means local development does not require an Inngest Cloud signing key. Production/cloud deployment should provide the real `INNGEST_SIGNING_KEY` and should not set `INNGEST_DEV=1`.