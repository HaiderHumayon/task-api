import type { StrictDecision } from "@/lib/decision-engine";

export type RunStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed";

export type RunLogEntry = {
  at: string;
  message: string;
  nodeId?: string;
  decision?: StrictDecision;
};

export type RunNodeResult = {
  nodeId: string;
  title: string;
  prompt: string;
  decision: StrictDecision;
  model: string;
};

export type DecisionRunState = {
  eventId: string;
  status: RunStatus;
  activeNodeId: string | null;
  executionOrder: string[];
  results: RunNodeResult[];
  logs: RunLogEntry[];
  terminalNodeId: string | null;
  error: string | null;
  updatedAt: string;
};

type RunStoreGlobal = typeof globalThis & {
  __decisionFlowRuns?: Map<
    string,
    DecisionRunState
  >;
};

const runtimeGlobal =
  globalThis as RunStoreGlobal;

const runs =
  runtimeGlobal.__decisionFlowRuns ??
  new Map<string, DecisionRunState>();

runtimeGlobal.__decisionFlowRuns = runs;

function now() {
  return new Date().toISOString();
}

export function createRun(
  eventId: string,
) {
  const state: DecisionRunState = {
    eventId,
    status: "queued",
    activeNodeId: null,
    executionOrder: [],
    results: [],
    logs: [
      {
        at: now(),
        message:
          "Workflow event accepted and queued.",
      },
    ],
    terminalNodeId: null,
    error: null,
    updatedAt: now(),
  };

  runs.set(eventId, state);
  return state;
}

export function getRun(
  eventId: string,
) {
  return runs.get(eventId) ?? null;
}

export function updateRun(
  eventId: string,
  updater: (
    current: DecisionRunState,
  ) => DecisionRunState,
) {
  const current =
    runs.get(eventId) ??
    createRun(eventId);

  const next = {
    ...updater(current),
    updatedAt: now(),
  };

  runs.set(eventId, next);
  return next;
}

export function markRunStarted(
  eventId: string,
) {
  return updateRun(
    eventId,
    (current) => ({
      ...current,
      status: "running",
      error: null,
      logs: [
        ...current.logs,
        {
          at: now(),
          message:
            "Inngest workflow started.",
        },
      ],
    }),
  );
}

export function markNodeActive(
  eventId: string,
  nodeId: string,
) {
  return updateRun(
    eventId,
    (current) => ({
      ...current,
      status: "running",
      activeNodeId: nodeId,
      logs: [
        ...current.logs,
        {
          at: now(),
          nodeId,
          message:
            `Executing ${nodeId} with the configured LLM.`,
        },
      ],
    }),
  );
}

export function recordNodeResult(
  eventId: string,
  result: RunNodeResult,
) {
  return updateRun(
    eventId,
    (current) => ({
      ...current,
      executionOrder: [
        ...current.executionOrder,
        result.nodeId,
      ],
      results: [
        ...current.results.filter(
          (item) =>
            item.nodeId !==
            result.nodeId,
        ),
        result,
      ],
      logs: [
        ...current.logs,
        {
          at: now(),
          nodeId: result.nodeId,
          decision:
            result.decision,
          message:
            `${result.nodeId} returned ${result.decision} using ${result.model}.`,
        },
      ],
    }),
  );
}

export function recordBranchFollowed(
  eventId: string,
  source: string,
  target: string,
  decision: StrictDecision,
) {
  return updateRun(
    eventId,
    (current) => ({
      ...current,
      logs: [
        ...current.logs,
        {
          at: now(),
          nodeId: source,
          decision,
          message:
            `Followed ${decision} branch: ${source} -> ${target}.`,
        },
      ],
    }),
  );
}

export function markRunCompleted(
  eventId: string,
  terminalNodeId: string,
) {
  return updateRun(
    eventId,
    (current) => ({
      ...current,
      status: "completed",
      activeNodeId: null,
      terminalNodeId,
      logs: [
        ...current.logs,
        {
          at: now(),
          nodeId:
            terminalNodeId,
          message:
            `Workflow completed at ${terminalNodeId}.`,
        },
      ],
    }),
  );
}

export function markRunFailed(
  eventId: string,
  error: string,
) {
  return updateRun(
    eventId,
    (current) => ({
      ...current,
      status: "failed",
      activeNodeId: null,
      error,
      logs: [
        ...current.logs,
        {
          at: now(),
          message:
            `Workflow failed: ${error}`,
        },
      ],
    }),
  );
}