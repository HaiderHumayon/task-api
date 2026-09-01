"use client";

import {
  useCallback,
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
  type Connection,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Bot,
  Cable,
  Check,
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

const branchVisuals = {
  YES: {
    stroke: "#34d399",
    text: "#6ee7b7",
    background: "#052e26",
  },
  NO: {
    stroke: "#fb7185",
    text: "#fda4af",
    background: "#4c0519",
  },
} satisfies Record<
  BranchType,
  {
    stroke: string;
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
  const visual = branchVisuals[branch];

  return {
    id,
    source,
    target,
    sourceHandle: branch.toLowerCase(),
    targetHandle: "input",
    type: "smoothstep",
    animated: true,
    label: branch,
    data: {
      branch,
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
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
      fill: visual.background,
      fillOpacity: 0.96,
    },
    labelBgPadding: [7, 4],
    labelBgBorderRadius: 6,
  };
}

const initialNodes: DecisionFlowNode[] = [
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
      title: "Confidence check",
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
      title: "Clarification check",
      prompt:
        "Would one focused clarification materially improve the quality of the final result?",
    },
  },
];

const initialEdges: DecisionFlowEdge[] = [
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
  if (connection.sourceHandle === "yes") {
    return "YES";
  }

  if (connection.sourceHandle === "no") {
    return "NO";
  }

  return null;
}

export function DecisionFlowBuilder() {
  const [nodes, setNodes, onNodesChange] =
    useNodesState<DecisionFlowNode>(initialNodes);
  const [edges, setEdges, onEdgesChange] =
    useEdgesState<DecisionFlowEdge>(initialEdges);
  const [selectedNodeId, setSelectedNodeId] =
    useState<string | null>("decision-1");
  const [branchMessage, setBranchMessage] =
    useState(
      "Connect from the green YES or red NO handle.",
    );
  const [dispatchMessage, setDispatchMessage] =
    useState("No workflow run dispatched yet.");
  const [isDispatching, setIsDispatching] =
    useState(false);
  const nextNodeNumber = useRef(4);
  const nextEdgeNumber = useRef(3);

  const updatePrompt = useCallback(
    (nodeId: string, prompt: string) => {
      setNodes((currentNodes) =>
        currentNodes.map((node) =>
          node.id === nodeId
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

  const displayNodes = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          onPromptChange: updatePrompt,
        },
      })),
    [nodes, updatePrompt],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      const branch =
        branchFromConnection(connection);

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
        connection.source === connection.target
      ) {
        setBranchMessage(
          "A decision cannot branch to itself.",
        );
        return;
      }

      const existingBranch = edges.find(
        (edge) =>
          edge.source === connection.source &&
          edge.data?.branch === branch,
      );

      if (existingBranch) {
        setBranchMessage(
          `${connection.source} already has a ${branch} branch. Delete or reconnect that edge first.`,
        );
        return;
      }

      const edgeNumber =
        nextEdgeNumber.current;
      nextEdgeNumber.current += 1;

      const newEdge = makeBranchEdge({
        id: `edge-${edgeNumber}-${branch.toLowerCase()}`,
        source: connection.source,
        target: connection.target,
        branch,
      });

      setEdges((currentEdges) =>
        addEdge(
          newEdge,
          currentEdges,
        ),
      );

      setBranchMessage(
        `${branch} branch connected: ${connection.source} → ${connection.target}`,
      );
    },
    [edges, setEdges],
  );

  const addDecisionNode = useCallback(() => {
    const number = nextNodeNumber.current;
    nextNodeNumber.current += 1;

    const nodeId = `decision-${number}`;

    const newNode: DecisionFlowNode = {
      id: nodeId,
      type: "decision",
      position: {
        x: 120 + ((number - 1) % 3) * 340,
        y:
          120 +
          Math.floor((number - 1) / 3) *
            280,
      },
      data: {
        title: `Decision ${number}`,
        prompt:
          "Write a clear question that the AI must answer with YES or NO.",
      },
    };

    setNodes((currentNodes) => [
      ...currentNodes,
      newNode,
    ]);
    setSelectedNodeId(nodeId);
    setBranchMessage(
      `${nodeId} added. Connect its YES and NO outcomes.`,
    );
  }, [setNodes]);

  const dispatchTestRun = useCallback(
    async (branch: BranchType) => {
      if (nodes.length === 0) {
        setDispatchMessage(
          "Add at least one node before running.",
        );
        return;
      }

      setIsDispatching(true);
      setDispatchMessage(
        `Dispatching deterministic ${branch} test run...`,
      );

      try {
        const payload = {
          nodes: nodes.map((node) => ({
            id: node.id,
            title: node.data.title,
            prompt: node.data.prompt,
          })),
          edges: edges.map((edge) => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            branch: edge.data?.branch,
          })),
          startNodeId: nodes[0].id,
          decisions: Object.fromEntries(
            nodes.map((node) => [
              node.id,
              branch,
            ]),
          ),
        };

        const response = await fetch(
          "/api/execute",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify(payload),
          },
        );

        const result = (await response.json()) as {
          accepted?: boolean;
          eventId?: string | null;
          error?: string;
        };

        if (!response.ok) {
          throw new Error(
            result.error ??
              `Dispatch failed with HTTP ${response.status}.`,
          );
        }

        setDispatchMessage(
          `Accepted by Inngest · event ${result.eventId ?? "queued"} · ${branch} test decisions`,
        );
      } catch (error) {
        setDispatchMessage(
          error instanceof Error
            ? error.message
            : "Workflow dispatch failed.",
        );
      } finally {
        setIsDispatching(false);
      }
    },
    [edges, nodes],
  );
  const selectedNode = nodes.find(
    (node) => node.id === selectedNodeId,
  );

  const yesCount = edges.filter(
    (edge) => edge.data?.branch === "YES",
  ).length;

  const noCount = edges.filter(
    (edge) => edge.data?.branch === "NO",
  ).length;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/95">
        <div className="mx-auto flex max-w-[1600px] flex-col gap-5 px-5 py-5 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-sky-300">
              <Sparkles size={14} />
              FlyRank · AI Decision Flow
            </div>

            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              YES / NO workflow builder
            </h1>

            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-400">
              Every decision has exactly two semantic outcomes. The branch value
              is stored on the edge and will drive execution in the Inngest
              workflow.
            </p>
          </div>

          <button
            type="button"
            onClick={addDecisionNode}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-sky-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-300"
          >
            <Plus size={17} />
            Add decision node
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1600px] gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_320px] lg:p-8">
        <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-slate-800 bg-slate-950/70 px-4 py-3 text-xs text-slate-400">
            <span className="inline-flex items-center gap-2">
              <MousePointer2 size={14} />
              Drag nodes
            </span>

            <span className="inline-flex items-center gap-2 text-emerald-300">
              <Check size={14} />
              Green handle = YES
            </span>

            <span className="inline-flex items-center gap-2 text-rose-300">
              <X size={14} />
              Red handle = NO
            </span>

            <span className="inline-flex items-center gap-2">
              <Cable size={14} />
              One branch of each type per node
            </span>
          </div>

          <div className="h-[740px]">
            <ReactFlow
              nodes={displayNodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={(_, node) => {
                setSelectedNodeId(node.id);
              }}
              onPaneClick={() => {
                setSelectedNodeId(null);
              }}
              fitView
              fitViewOptions={{
                padding: 0.18,
              }}
              minZoom={0.35}
              maxZoom={1.8}
              proOptions={{
                hideAttribution: false,
              }}
            >
              <Background
                variant={BackgroundVariant.Dots}
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
                <div className="flex items-center gap-2 text-emerald-300">
                  <Check size={15} />
                  <span className="text-sm font-semibold">
                    YES
                  </span>
                </div>
                <div className="mt-2 text-xl font-semibold text-white">
                  {yesCount}
                </div>
              </div>

              <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-3">
                <div className="flex items-center gap-2 text-rose-300">
                  <X size={15} />
                  <span className="text-sm font-semibold">
                    NO
                  </span>
                </div>
                <div className="mt-2 text-xl font-semibold text-white">
                  {noCount}
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="flex items-center gap-2">
              <GitBranch
                size={17}
                className="text-violet-300"
              />
              <h2 className="font-semibold text-white">
                Branch rule
              </h2>
            </div>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              Each source node can have at most one YES branch and one NO branch.
              The value is stored in <code>edge.data.branch</code>.
            </p>

            <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs leading-5 text-slate-300">
              {branchMessage}
            </div>
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
              <Play
                size={17}
                className="text-amber-300"
              />
              <h2 className="font-semibold text-white">
                Inngest test run
              </h2>
            </div>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              Stage 3 uses deterministic decisions so traversal can be tested
              before the LLM is connected.
            </p>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <button
                type="button"
                disabled={isDispatching}
                onClick={() => {
                  void dispatchTestRun("YES");
                }}
                className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-3 text-sm font-semibold text-emerald-200 transition hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Test YES path
              </button>

              <button
                type="button"
                disabled={isDispatching}
                onClick={() => {
                  void dispatchTestRun("NO");
                }}
                className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-3 text-sm font-semibold text-rose-200 transition hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Test NO path
              </button>
            </div>

            <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs leading-5 text-slate-300">
              {dispatchMessage}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <h2 className="font-semibold text-white">
              Stage 3 checkpoint
            </h2>

            <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-400">
              <li>✓ Typed Inngest execution event</li>
              <li>✓ POST /api/execute dispatcher</li>
              <li>✓ Graph validation before dispatch</li>
              <li>✓ One step.run per visited node</li>
              <li>✓ YES / NO edge traversal</li>
              <li>✓ Execution-order tracking</li>
              <li>✓ Cycle protection</li>
            </ul>

            <p className="mt-4 rounded-xl border border-violet-500/20 bg-violet-500/5 p-3 text-xs leading-5 text-violet-200">
              Next: replace deterministic test decisions with a real LLM call
              that must return only YES or NO.
            </p>
          </section>
        </aside>
      </div>
    </main>
  );
}