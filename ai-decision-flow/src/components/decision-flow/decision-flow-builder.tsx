"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Connection,
  type Edge,
  type Node,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Bot,
  Cable,
  MousePointer2,
  Network,
  Plus,
  Sparkles,
} from "lucide-react";

import { DecisionNode } from "./decision-node";
import type {
  DecisionFlowEdge,
  DecisionFlowNode,
} from "./types";

const initialNodes: DecisionFlowNode[] = [
  {
    id: "decision-1",
    type: "decision",
    position: { x: 80, y: 90 },
    data: {
      title: "Intent check",
      prompt:
        "Does the user's request clearly describe a task that can be completed with the available information?",
    },
  },
  {
    id: "decision-2",
    type: "decision",
    position: { x: 470, y: 300 },
    data: {
      title: "Risk check",
      prompt:
        "Would completing this request create a meaningful safety, privacy, or compliance risk?",
    },
  },
  {
    id: "decision-3",
    type: "decision",
    position: { x: 860, y: 510 },
    data: {
      title: "Action check",
      prompt:
        "Is there enough confidence to continue to the final action without asking a follow-up question?",
    },
  },
];

const initialEdges: DecisionFlowEdge[] = [
  {
    id: "edge-1-2",
    source: "decision-1",
    target: "decision-2",
    animated: true,
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
    style: {
      strokeWidth: 2,
    },
  },
  {
    id: "edge-2-3",
    source: "decision-2",
    target: "decision-3",
    animated: true,
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
    style: {
      strokeWidth: 2,
    },
  },
];

const nodeTypes = {
  decision: DecisionNode,
};

export function DecisionFlowBuilder() {
  const [nodes, setNodes, onNodesChange] =
    useNodesState<DecisionFlowNode>(initialNodes);
  const [edges, setEdges, onEdgesChange] =
    useEdgesState<DecisionFlowEdge>(initialEdges);
  const [selectedNodeId, setSelectedNodeId] =
    useState<string | null>("decision-1");
  const nextNodeNumber = useRef(4);

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
      setEdges((currentEdges) =>
        addEdge(
          {
            ...connection,
            animated: true,
            markerEnd: {
              type: MarkerType.ArrowClosed,
            },
            style: {
              strokeWidth: 2,
            },
          },
          currentEdges,
        ),
      );
    },
    [setEdges],
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
        y: 120 + Math.floor((number - 1) / 3) * 260,
      },
      data: {
        title: `Decision ${number}`,
        prompt:
          "Write a clear question that this AI decision node should evaluate.",
      },
    };

    setNodes((currentNodes) => [
      ...currentNodes,
      newNode,
    ]);
    setSelectedNodeId(nodeId);
  }, [setNodes]);

  const selectedNode = nodes.find(
    (node) => node.id === selectedNodeId,
  );

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
              Visual workflow builder
            </h1>

            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-400">
              Build the graph visually now. In later stages each decision node
              becomes an executable Inngest step powered by an LLM.
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

      <div className="mx-auto grid max-w-[1600px] gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_310px] lg:p-8">
        <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-slate-800 bg-slate-950/70 px-4 py-3 text-xs text-slate-400">
            <span className="inline-flex items-center gap-2">
              <MousePointer2 size={14} />
              Drag nodes
            </span>

            <span className="inline-flex items-center gap-2">
              <Cable size={14} />
              Drag handle to connect
            </span>

            <span className="inline-flex items-center gap-2">
              <Bot size={14} />
              Edit prompts inline
            </span>
          </div>

          <div className="h-[720px]">
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
              defaultEdgeOptions={{
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                },
              }}
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
                  Connections
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <h2 className="font-semibold text-white">
              Selected node
            </h2>

            {selectedNode ? (
              <div className="mt-4">
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
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

                <p className="mt-3 text-xs leading-5 text-slate-500">
                  Edit the prompt directly inside the node on the canvas.
                </p>
              </div>
            ) : (
              <p className="mt-3 text-sm leading-6 text-slate-500">
                Click a node to inspect it here.
              </p>
            )}
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <h2 className="font-semibold text-white">
              Stage 1 checkpoint
            </h2>

            <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-400">
              <li>✓ React Flow canvas</li>
              <li>✓ Add decision nodes</li>
              <li>✓ Move nodes</li>
              <li>✓ Connect nodes</li>
              <li>✓ Edit prompts inline</li>
              <li>✓ Controlled local graph state</li>
            </ul>

            <p className="mt-4 rounded-xl border border-violet-500/20 bg-violet-500/5 p-3 text-xs leading-5 text-violet-200">
              Next stage: every outgoing connection becomes an explicit YES or
              NO branch.
            </p>
          </section>
        </aside>
      </div>
    </main>
  );
}