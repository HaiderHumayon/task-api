"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Connection,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Activity,
  Cable,
  Check,
  CircleStop,
  Clock3,
  GitBranch,
  MousePointer2,
  Network,
  Play,
  Plus,
  Sparkles,
  X,
} from "lucide-react";

import { DecisionNode } from "./decision-node";
import type {
  BranchType,
  DecisionFlowEdge,
  DecisionFlowNode,
} from "./types";

type RunNodeResult = {
  nodeId: string;
  title: string;
  prompt: string;
  decision: BranchType;
  model: string;
};

type RunLogEntry = {
  at: string;
  message: string;
  nodeId?: string;
  decision?: BranchType;
};

type RunState = {
  eventId: string;
  status:
    | "queued"
    | "running"
    | "completed"
    | "failed";
  activeNodeId: string | null;
  executionOrder: string[];
  results: RunNodeResult[];
  logs: RunLogEntry[];
  terminalNodeId: string | null;
  error: string | null;
  updatedAt: string;
};

const branchVisuals = {
  YES: {
    stroke: "#34d399",
    activeStroke: "#6ee7b7",
    text: "#6ee7b7",
    background: "#052e26",
  },
  NO: {
    stroke: "#fb7185",
    activeStroke: "#fda4af",
    text: "#fda4af",
    background: "#4c0519",
  },
} satisfies Record<
  BranchType,
  {
    stroke: string;
    activeStroke: string;
    text: string;
    background: string;
  }
>;

function makeBranchEdge({
  id,
  source,
  target,
  branch,
}: {
  id: string;
  source: string;
  target: string;
  branch: BranchType;
}): DecisionFlowEdge {
  const visual =
    branchVisuals[branch];

  return {
    id,
    source,
    target,
    sourceHandle:
      branch.toLowerCase(),
    targetHandle: "input",
    type: "smoothstep",
    animated: true,
    label: branch,
    data: {
      branch,
    },
    markerEnd: {
      type:
        MarkerType.ArrowClosed,
      color: visual.stroke,
    },
    style: {
      stroke: visual.stroke,
      strokeWidth: 2.5,
    },
    labelStyle: {
      fill: visual.text,
      fontWeight: 800,
      fontSize: 11,
    },
    labelBgStyle: {
      fill:
        visual.background,
      fillOpacity: 0.96,
    },
    labelBgPadding: [7, 4],
    labelBgBorderRadius: 6,
  };
}

const initialNodes:
  DecisionFlowNode[] = [
  {
    id: "decision-1",
    type: "decision",
    position: {
      x: 390,
      y: 60,
    },
    data: {
      title: "Intent check",
      prompt:
        "Does the user's request clearly describe a task that can be completed with the available information?",
    },
  },
  {
    id: "decision-2",
    type: "decision",
    position: {
      x: 100,
      y: 390,
    },
    data: {
      title:
        "Confidence check",
      prompt:
        "Is there enough information and confidence to continue without asking the user a follow-up question?",
    },
  },
  {
    id: "decision-3",
    type: "decision",
    position: {
      x: 700,
      y: 390,
    },
    data: {
      title:
        "Clarification check",
      prompt:
        "Would one focused clarification materially improve the quality of the final result?",
    },
  },
];

const initialEdges:
  DecisionFlowEdge[] = [
  makeBranchEdge({
    id: "edge-1-yes-2",
    source: "decision-1",
    target: "decision-2",
    branch: "YES",
  }),
  makeBranchEdge({
    id: "edge-1-no-3",
    source: "decision-1",
    target: "decision-3",
    branch: "NO",
  }),
];

const nodeTypes = {
  decision: DecisionNode,
};

function branchFromConnection(
  connection: Connection,
): BranchType | null {
  if (
    connection.sourceHandle ===
    "yes"
  ) {
    return "YES";
  }

  if (
    connection.sourceHandle ===
    "no"
  ) {
    return "NO";
  }

  return null;
}

function edgeWasTraversed(
  edge: DecisionFlowEdge,
  results: RunNodeResult[],
) {
  const sourceResult =
    results.find(
      (result) =>
        result.nodeId ===
        edge.source,
    );

  return (
    sourceResult?.decision ===
    edge.data?.branch
  );
}

export function DecisionFlowBuilder() {
  const [
    nodes,
    setNodes,
    onNodesChange,
  ] =
    useNodesState<DecisionFlowNode>(
      initialNodes,
    );
  const [
    edges,
    setEdges,
    onEdgesChange,
  ] =
    useEdgesState<DecisionFlowEdge>(
      initialEdges,
    );

  const [
    selectedNodeId,
    setSelectedNodeId,
  ] =
    useState<string | null>(
      "decision-1",
    );
  const [
    branchMessage,
    setBranchMessage,
  ] = useState(
    "Connect from the green YES or red NO handle.",
  );
  const [
    dispatchMessage,
    setDispatchMessage,
  ] = useState(
    "No workflow run dispatched yet.",
  );
  const [
    isDispatching,
    setIsDispatching,
  ] = useState(false);
  const [
    runState,
    setRunState,
  ] =
    useState<RunState | null>(
      null,
    );
  const [
    activeEventId,
    setActiveEventId,
  ] =
    useState<string | null>(
      null,
    );

  const nextNodeNumber =
    useRef(4);
  const nextEdgeNumber =
    useRef(3);

  const updatePrompt =
    useCallback(
      (
        nodeId: string,
        prompt: string,
      ) => {
        setNodes(
          (currentNodes) =>
            currentNodes.map(
              (node) =>
                node.id ===
                nodeId
                  ? {
                      ...node,
                      data: {
                        ...node.data,
                        prompt,
                      },
                    }
                  : node,
            ),
        );
      },
      [setNodes],
    );

  const displayNodes =
    useMemo(
      () =>
        nodes.map((node) => {
          const result =
            runState?.results.find(
              (item) =>
                item.nodeId ===
                node.id,
            );

          const isActive =
            runState
              ?.activeNodeId ===
            node.id;

          const wasVisited =
            runState?.executionOrder.includes(
              node.id,
            );

          return {
            ...node,
            data: {
              ...node.data,
              onPromptChange:
                updatePrompt,
              executionStatus:
                isActive
                  ? "active"
                  : wasVisited
                    ? "visited"
                    : "idle",
              lastDecision:
                result?.decision,
            },
          } satisfies DecisionFlowNode;
        }),
      [
        nodes,
        runState,
        updatePrompt,
      ],
    );

  const displayEdges =
    useMemo(
      () =>
        edges.map((edge) => {
          const branch =
            edge.data?.branch;

          if (!branch) {
            return edge;
          }

          const visual =
            branchVisuals[
              branch
            ];

          const traversed =
            edgeWasTraversed(
              edge,
              runState?.results ??
                [],
            );

          return {
            ...edge,
            animated: traversed,
            markerEnd: {
              type:
                MarkerType.ArrowClosed,
              color: traversed
                ? visual.activeStroke
                : visual.stroke,
            },
            style: {
              stroke: traversed
                ? visual.activeStroke
                : visual.stroke,
              strokeWidth:
                traversed
                  ? 4
                  : 2.5,
              opacity:
                runState &&
                !traversed
                  ? 0.35
                  : 1,
            },
          };
        }),
      [edges, runState],
    );

  const onConnect =
    useCallback(
      (
        connection: Connection,
      ) => {
        const branch =
          branchFromConnection(
            connection,
          );

        if (
          !branch ||
          !connection.source ||
          !connection.target
        ) {
          setBranchMessage(
            "Use one of the labeled YES / NO source handles.",
          );
          return;
        }

        if (
          connection.source ===
          connection.target
        ) {
          setBranchMessage(
            "A decision cannot branch to itself.",
          );
          return;
        }

        const existingBranch =
          edges.find(
            (edge) =>
              edge.source ===
                connection.source &&
              edge.data?.branch ===
                branch,
          );

        if (existingBranch) {
          setBranchMessage(
            `${connection.source} already has a ${branch} branch.`,
          );
          return;
        }

        const edgeNumber =
          nextEdgeNumber.current;
        nextEdgeNumber.current +=
          1;

        const newEdge =
          makeBranchEdge({
            id: `edge-${edgeNumber}-${branch.toLowerCase()}`,
            source:
              connection.source,
            target:
              connection.target,
            branch,
          });

        setEdges(
          (currentEdges) =>
            addEdge(
              newEdge,
              currentEdges,
            ),
        );

        setBranchMessage(
          `${branch} branch connected: ${connection.source} -> ${connection.target}`,
        );
      },
      [edges, setEdges],
    );

  const addDecisionNode =
    useCallback(() => {
      const number =
        nextNodeNumber.current;
      nextNodeNumber.current +=
        1;

      const nodeId =
        `decision-${number}`;

      const newNode:
        DecisionFlowNode = {
        id: nodeId,
        type: "decision",
        position: {
          x:
            120 +
            ((number - 1) % 3) *
              340,
          y:
            120 +
            Math.floor(
              (number - 1) /
                3,
            ) *
              280,
        },
        data: {
          title:
            `Decision ${number}`,
          prompt:
            "Write a clear question that the AI must answer with YES or NO.",
        },
      };

      setNodes(
        (currentNodes) => [
          ...currentNodes,
          newNode,
        ],
      );
      setSelectedNodeId(
        nodeId,
      );
      setBranchMessage(
        `${nodeId} added. Connect its YES and NO outcomes.`,
      );
    }, [setNodes]);

  const dispatchAiRun =
    useCallback(async () => {
      if (nodes.length === 0) {
        setDispatchMessage(
          "Add at least one node before running.",
        );
        return;
      }

      const invalidPrompt =
        nodes.find(
          (node) =>
            !node.data.prompt.trim(),
        );

      if (invalidPrompt) {
        setDispatchMessage(
          `${invalidPrompt.id} needs a prompt before execution.`,
        );
        return;
      }

      setIsDispatching(true);
      setRunState(null);
      setActiveEventId(null);
      setDispatchMessage(
        "Dispatching graph to Inngest for real LLM decisions...",
      );

      try {
        const payload = {
          nodes: nodes.map(
            (node) => ({
              id: node.id,
              title:
                node.data.title,
              prompt:
                node.data.prompt,
            }),
          ),
          edges: edges.map(
            (edge) => ({
              id: edge.id,
              source:
                edge.source,
              target:
                edge.target,
              branch:
                edge.data
                  ?.branch,
            }),
          ),
          startNodeId:
            nodes[0].id,
        };

        const response =
          await fetch(
            "/api/execute",
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/json",
              },
              body:
                JSON.stringify(
                  payload,
                ),
            },
          );

        const result =
          (await response.json()) as {
            accepted?: boolean;
            eventId?:
              string | null;
            error?: string;
          };

        if (!response.ok) {
          throw new Error(
            result.error ??
              `Dispatch failed with HTTP ${response.status}.`,
          );
        }

        if (!result.eventId) {
          throw new Error(
            "Inngest accepted the event but did not return an event ID.",
          );
        }

        setActiveEventId(
          result.eventId,
        );
        setDispatchMessage(
          `Accepted by Inngest · event ${result.eventId}`,
        );
      } catch (error) {
        setDispatchMessage(
          error instanceof Error
            ? error.message
            : "Workflow dispatch failed.",
        );
      } finally {
        setIsDispatching(
          false,
        );
      }
    }, [edges, nodes]);

  useEffect(() => {
    if (!activeEventId) {
      return;
    }

    let cancelled = false;
    let timer:
      ReturnType<
        typeof setTimeout
      >;

    const poll = async () => {
      try {
        const response =
          await fetch(
            `/api/runs/${encodeURIComponent(activeEventId)}`,
            {
              cache:
                "no-store",
            },
          );

        if (response.ok) {
          const state =
            (await response.json()) as RunState;

          if (!cancelled) {
            setRunState(state);
          }

          if (
            state.status ===
              "completed" ||
            state.status ===
              "failed"
          ) {
            if (!cancelled) {
              setDispatchMessage(
                state.status ===
                  "completed"
                  ? `Run complete · ${state.executionOrder.length} node(s) visited`
                  : `Run failed · ${state.error ?? "unknown error"}`,
              );
            }
            return;
          }
        }
      } catch {
        // A transient poll failure should not stop
        // the execution itself.
      }

      if (!cancelled) {
        timer = setTimeout(
          poll,
          900,
        );
      }
    };

    void poll();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [activeEventId]);

  const selectedNode =
    nodes.find(
      (node) =>
        node.id ===
        selectedNodeId,
    );

  const yesCount =
    edges.filter(
      (edge) =>
        edge.data?.branch ===
        "YES",
    ).length;

  const noCount =
    edges.filter(
      (edge) =>
        edge.data?.branch ===
        "NO",
    ).length;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/95">
        <div className="mx-auto flex max-w-[1700px] flex-col gap-5 px-5 py-5 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-sky-300">
              <Sparkles size={14} />
              FlyRank · AI Decision Flow
            </div>

            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              Executable AI workflow builder
            </h1>

            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-400">
              Build the graph, run it through Inngest, and watch the LLM decisions
              light up the exact path that execution follows.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={
                addDecisionNode
              }
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:border-slate-600"
            >
              <Plus size={17} />
              Add decision node
            </button>

            <button
              type="button"
              disabled={
                isDispatching ||
                runState?.status ===
                  "running"
              }
              onClick={() => {
                void dispatchAiRun();
              }}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-amber-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Play size={17} />
              {runState?.status ===
              "running"
                ? "Running..."
                : "Run with AI"}
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1700px] gap-5 p-5 xl:grid-cols-[minmax(0,1fr)_360px] xl:p-8">
        <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-slate-800 bg-slate-950/70 px-4 py-3 text-xs text-slate-400">
            <span className="inline-flex items-center gap-2">
              <MousePointer2 size={14} />
              Drag nodes
            </span>

            <span className="inline-flex items-center gap-2 text-emerald-300">
              <Check size={14} />
              Green = YES
            </span>

            <span className="inline-flex items-center gap-2 text-rose-300">
              <X size={14} />
              Red = NO
            </span>

            <span className="inline-flex items-center gap-2 text-amber-300">
              <Activity size={14} />
              Amber = active
            </span>

            <span className="inline-flex items-center gap-2 text-violet-300">
              <GitBranch size={14} />
              Thick edge = traversed
            </span>
          </div>

          <div className="h-[760px]">
            <ReactFlow
              nodes={displayNodes}
              edges={displayEdges}
              nodeTypes={nodeTypes}
              onNodesChange={
                onNodesChange
              }
              onEdgesChange={
                onEdgesChange
              }
              onConnect={
                onConnect
              }
              onNodeClick={(
                _,
                node,
              ) => {
                setSelectedNodeId(
                  node.id,
                );
              }}
              onPaneClick={() => {
                setSelectedNodeId(
                  null,
                );
              }}
              fitView
              fitViewOptions={{
                padding: 0.18,
              }}
              minZoom={0.35}
              maxZoom={1.8}
              proOptions={{
                hideAttribution:
                  false,
              }}
            >
              <Background
                variant={
                  BackgroundVariant.Dots
                }
                gap={22}
                size={1.5}
              />
              <MiniMap
                pannable
                zoomable
                nodeStrokeWidth={3}
              />
              <Controls />
            </ReactFlow>
          </div>
        </section>

        <aside className="space-y-5">
          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Activity
                  size={17}
                  className="text-amber-300"
                />
                <h2 className="font-semibold text-white">
                  Execution
                </h2>
              </div>

              <span
                className={[
                  "rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]",
                  runState?.status ===
                  "completed"
                    ? "bg-emerald-500/10 text-emerald-300"
                    : runState?.status ===
                        "failed"
                      ? "bg-rose-500/10 text-rose-300"
                      : runState?.status ===
                          "running"
                        ? "bg-amber-500/10 text-amber-300"
                        : "bg-slate-800 text-slate-400",
                ].join(" ")}
              >
                {runState?.status ??
                  "idle"}
              </span>
            </div>

            <p className="mt-3 break-all text-xs leading-5 text-slate-500">
              {activeEventId
                ? `Event: ${activeEventId}`
                : "No active event"}
            </p>

            <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs leading-5 text-slate-300">
              {dispatchMessage}
            </div>

            {runState?.executionOrder
              .length ? (
              <div className="mt-4">
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
                  Execution order
                </p>

                <div className="mt-2 flex flex-wrap gap-2">
                  {runState.executionOrder.map(
                    (
                      nodeId,
                      index,
                    ) => (
                      <span
                        key={`${nodeId}-${index}`}
                        className="rounded-lg border border-violet-500/20 bg-violet-500/5 px-2 py-1 text-xs text-violet-200"
                      >
                        {index + 1}.{" "}
                        {nodeId}
                      </span>
                    ),
                  )}
                </div>
              </div>
            ) : null}
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="flex items-center gap-2">
              <Clock3
                size={17}
                className="text-sky-300"
              />
              <h2 className="font-semibold text-white">
                Live log
              </h2>
            </div>

            <div className="mt-4 max-h-[310px] space-y-3 overflow-y-auto pr-1">
              {runState?.logs
                .length ? (
                runState.logs.map(
                  (
                    log,
                    index,
                  ) => (
                    <div
                      key={`${log.at}-${index}`}
                      className="rounded-xl border border-slate-800 bg-slate-950 p-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] text-slate-600">
                          {new Date(
                            log.at,
                          ).toLocaleTimeString()}
                        </span>

                        {log.decision ? (
                          <span
                            className={
                              log.decision ===
                              "YES"
                                ? "text-[10px] font-bold text-emerald-300"
                                : "text-[10px] font-bold text-rose-300"
                            }
                          >
                            {log.decision}
                          </span>
                        ) : null}
                      </div>

                      <p className="mt-1 text-xs leading-5 text-slate-300">
                        {log.message}
                      </p>
                    </div>
                  ),
                )
              ) : (
                <p className="text-sm leading-6 text-slate-500">
                  Run the graph to see execution logs here.
                </p>
              )}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="flex items-center gap-2">
              <Network
                size={17}
                className="text-sky-300"
              />
              <h2 className="font-semibold text-white">
                Graph state
              </h2>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <div className="text-2xl font-semibold text-white">
                  {nodes.length}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Nodes
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <div className="text-2xl font-semibold text-white">
                  {edges.length}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Branches
                </div>
              </div>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
                <div className="text-xs text-emerald-300">
                  YES branches
                </div>
                <div className="mt-1 text-xl font-semibold">
                  {yesCount}
                </div>
              </div>

              <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-3">
                <div className="text-xs text-rose-300">
                  NO branches
                </div>
                <div className="mt-1 text-xl font-semibold">
                  {noCount}
                </div>
              </div>
            </div>

            <p className="mt-3 rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs leading-5 text-slate-400">
              {branchMessage}
            </p>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <h2 className="font-semibold text-white">
              Selected node
            </h2>

            {selectedNode ? (
              <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-300">
                  {selectedNode.id}
                </p>

                <p className="mt-2 font-medium text-white">
                  {selectedNode.data.title}
                </p>

                <p className="mt-2 line-clamp-5 text-sm leading-6 text-slate-400">
                  {selectedNode.data.prompt}
                </p>
              </div>
            ) : (
              <p className="mt-3 text-sm leading-6 text-slate-500">
                Click a node to inspect it.
              </p>
            )}
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="flex items-center gap-2">
              <CircleStop
                size={17}
                className="text-violet-300"
              />
              <h2 className="font-semibold text-white">
                Stage 5 checkpoint
              </h2>
            </div>

            <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-400">
              <li>✓ queued / running / completed / failed state</li>
              <li>✓ active node highlight</li>
              <li>✓ visited node styling</li>
              <li>✓ traversed edge highlighting</li>
              <li>✓ execution-order chips</li>
              <li>✓ live run log</li>
              <li>✓ per-node YES / NO result badge</li>
              <li>✓ polling by Inngest event ID</li>
            </ul>

            <p className="mt-4 rounded-xl border border-violet-500/20 bg-violet-500/5 p-3 text-xs leading-5 text-violet-200">
              Next: persistence, JSON import/export, final validation, live proof,
              and submission documentation.
            </p>
          </section>
        </aside>
      </div>
    </main>
  );
}