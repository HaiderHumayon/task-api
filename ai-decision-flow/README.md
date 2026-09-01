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
## Stage 1 — visual canvas

The placeholder page is replaced with a controlled React Flow workspace.

Implemented in this stage:

- three starter decision nodes
- drag/reposition nodes
- connect nodes by dragging source/target handles
- add new decision nodes
- edit each prompt directly inside its node
- local controlled node/edge state with `useNodesState` and `useEdgesState`
- animated arrow connections
- zoom/pan controls
- minimap
- selected-node summary
- live node and connection counts

The node data currently stores a title and prompt. The graph remains entirely local in Stage 1.

Stage 2 adds explicit `YES` and `NO` branch semantics to outgoing edges.
## Stage 2 — YES / NO branches

Decision nodes now expose two explicit source handles:

- green `YES`
- red `NO`

Every branch stores its semantic value in graph state:

```ts
type BranchType = "YES" | "NO";

type BranchEdgeData = {
  branch: BranchType;
};
```

The connection handler derives the branch from the source handle and writes it to `edge.data.branch`.

Additional Stage 2 rules:

- one YES branch maximum per source node
- one NO branch maximum per source node
- self-loop connections are rejected
- YES and NO branches use distinct colors and labels
- the sidebar shows live YES/NO branch counts

This means the graph is now executable in principle: once a decision produces `YES` or `NO`, the workflow can select the edge whose `data.branch` matches that result.

Stage 3 sends this graph to Inngest and implements deterministic traversal with a durable step for each visited node.