import type { Edge, Node } from "@xyflow/react";

export type BranchType = "YES" | "NO";

export type NodeExecutionStatus =
  | "idle"
  | "active"
  | "visited";

export type DecisionNodeData = {
  title: string;
  prompt: string;
  executionStatus?: NodeExecutionStatus;
  lastDecision?: BranchType;
  onPromptChange?: (
    nodeId: string,
    prompt: string,
  ) => void;
};

export type DecisionFlowNode =
  Node<
    DecisionNodeData,
    "decision"
  >;

export type BranchEdgeData = {
  branch: BranchType;
};

export type DecisionFlowEdge =
  Edge<BranchEdgeData>;