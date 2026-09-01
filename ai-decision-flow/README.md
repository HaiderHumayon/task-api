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
## Stage 3 — Inngest traversal

The graph is now dispatchable as an Inngest event:

```text
decision-flow/execute
```

`POST /api/execute` validates the graph and sends the event to Inngest.

The event contains:

- nodes
- edges
- start node ID
- deterministic Stage 3 decision values

The registered `execute-decision-flow` Inngest function:

1. starts at `startNodeId`
2. runs each visited node inside its own durable `step.run(...)`
3. records the node ID in `executionOrder`
4. reads the node's Stage 3 deterministic `YES` or `NO`
5. finds the outgoing edge whose `branch` matches that decision
6. follows the edge to the next node
7. stops when no matching outgoing branch exists
8. rejects cycles

The Stage 3 UI exposes `Test YES path` and `Test NO path` buttons. These deterministic values exist only to prove traversal before LLM integration.

For local execution, run the Next.js app with Inngest development mode and start the Inngest Dev Server in a second terminal:

```powershell
$env:INNGEST_DEV="1"
npm run dev
```

```powershell
npx --ignore-scripts=false inngest-cli@latest dev -u http://localhost:3000/api/inngest
```

The local Inngest dashboard is available at:

```text
http://localhost:8288
```

Stage 4 replaces the deterministic decision map with an OpenAI SDK call at each visited node and validates a strict `YES` or `NO` response.
## Stage 4 — real LLM decisions

Each visited graph node now calls the OpenAI SDK inside its own Inngest `step.run(...)`.

The node prompt is sent to the LLM with a system instruction that requires exactly one binary output:

```text
YES
```

or:

```text
NO
```

`parseStrictDecision()` validates the returned text with Zod. Any other output throws an error, which allows the Inngest function retry policy to handle the failed execution rather than silently guessing a branch.

### Environment

Create a local `.env.local` file:

```env
INNGEST_DEV=1
OPENAI_API_KEY=your-key-here
OPENAI_BASE_URL=
OPENAI_MODEL=
```

`OPENAI_BASE_URL` is optional. Leave it empty for OpenAI or set it to an OpenAI-compatible provider endpoint.

`OPENAI_MODEL` is optional and defaults to:

```text
gpt-4o-mini
```

Real `.env` and `.env.local` files remain ignored by Git.

### Execution

The workflow now:

1. receives the graph through `decision-flow/execute`
2. starts at the first node sent by the UI
3. executes that node inside `step.run(...)`
4. sends the node prompt to the LLM
5. accepts only `YES` or `NO`
6. records the decision and model
7. selects the outgoing edge with the matching `edge.branch`
8. continues until no matching edge exists
9. returns the complete execution order and node results

The Stage 4 UI exposes one `Run with AI` action rather than deterministic test controls.

A real API key is intentionally not stored or committed. Final live execution evidence is added in the later execution/polish stage.
## Stage 5 — execution state and logs

The UI now tracks the state of an Inngest execution instead of stopping after event dispatch.

`POST /api/execute` creates an in-memory run record keyed by the returned Inngest event ID.

The Inngest workflow updates that run state while traversing the graph:

- queued
- running
- active node
- node result
- branch followed
- completed
- failed

The UI polls:

```text
GET /api/runs/{eventId}
```

and renders:

- current run status
- active-node highlight
- visited-node styling
- per-node last decision
- traversed-edge emphasis
- execution order
- live execution log
- terminal/failure state

The state store is intentionally lightweight and process-local for this internship assignment. A production multi-instance deployment would move execution state to a shared persistent store such as PostgreSQL, Redis, or another durable database.
## Stage 6 — save, load, import, export

The graph is now portable and recoverable.

### Browser save/load

`Save` writes a clean workflow snapshot to `localStorage` under:

```text
ai-decision-flow:graph:v1
```

`Load` restores the saved graph.

Execution-only UI state is deliberately excluded from the saved workflow.

### JSON export/import

`Export JSON` downloads:

```text
ai-decision-flow.json
```

The portable format contains:

- format version
- save timestamp
- decision node IDs
- node positions
- node titles
- node prompts
- branch edge IDs
- source/target node IDs
- YES/NO branch values

`Import JSON` validates the file before replacing the current graph.

Import validation rejects:

- unsupported format versions
- malformed nodes
- duplicate node IDs
- malformed edges
- edges referencing missing nodes
- self-loops
- more than one YES branch from a source node
- more than one NO branch from a source node

Importing or loading a workflow clears stale execution-state overlays before the restored graph is displayed.

At this point the assignment includes multiple polish features beyond the required canvas:

1. live execution state and logs
2. active/visited path visualization
3. browser save/load
4. JSON import/export
5. error validation and Inngest retries

The remaining checkpoint is final live proof with an actual configured LLM and the local Inngest Dev Server.
## Reasoning-model compatibility

The decision engine uses `max_completion_tokens` rather than the deprecated `max_tokens` field.

A larger completion budget is intentional because reasoning models such as GPT-OSS may spend generated tokens on internal reasoning before emitting the final answer. The final `message.content` is still validated strictly and must contain exactly:

```text
YES
```

or:

```text
NO
```

The user instruction and the decision prompt are sent together as a single user message for broad OpenAI-compatible-provider support.
## Final live proof

A real LLM + Inngest execution completed successfully during the final submission audit.

Verified end-to-end behavior:

- `GET /api/health` returned HTTP `200`
- `GET /api/inngest` returned HTTP `200` in local development mode
- Inngest Dev Server connected to the Next.js serve endpoint
- `POST /api/execute` returned HTTP `202`
- real OpenAI SDK calls executed inside Inngest `step.run(...)`
- strict binary decisions observed: `YES`, `NO`, `YES`
- execution order: `proof-1 -> proof-2 -> proof-3`
- YES edge traversal verified
- NO edge traversal verified
- execution state reached `completed`
- the configured model was recorded in execution results

Evidence:

- [`docs/live-proof.md`](./docs/live-proof.md)
- [`docs/live-proof.json`](./docs/live-proof.json)
- [`docs/sample-workflow.json`](./docs/sample-workflow.json)

No API key or `.env.local` content is committed.

## Assignment acceptance checklist

### Required stack

- Next.js + TypeScript
- React Flow via `@xyflow/react`
- Inngest
- OpenAI SDK
- Shadcn component system
- environment-variable configuration

### Visual workflow

- add decision nodes
- move nodes
- connect nodes
- edit prompts inline
- explicit YES and NO source handles
- color-coded and labeled YES/NO edges
- controlled local graph state

### Execution

- graph dispatched through `decision-flow/execute`
- one durable `step.run(...)` for every visited node
- current node prompt sent to the configured LLM
- model output validated as exactly YES or NO
- matching YES/NO edge selected
- graph traversal continues until a terminal node
- execution order tracked
- cycle protection
- Inngest retries

### Polish

The project includes more than three polish features:

1. queued/running/completed/failed execution states
2. live execution logs
3. active-node and visited-node visualization
4. traversed-edge highlighting
5. per-node decision badges
6. browser save/load
7. JSON import/export
8. import validation and error handling

### Shadcn integration

The UI now includes the standard Shadcn component configuration in `components.json`, the shared `cn()` utility, and a source-owned Shadcn `Button` component built with `class-variance-authority` and Radix Slot. The workflow-builder actions use that component directly.

### Production note

The assignment run-state store is intentionally process-local. A multi-instance production deployment should replace it with shared durable storage such as PostgreSQL or Redis. Inngest remains responsible for durable workflow execution and retries.