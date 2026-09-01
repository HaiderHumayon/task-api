import type { Edge, Node } from "@xyflow/react";

export type DecisionNodeData = {
  title: string;
  prompt: string;
  onPromptChange?: (nodeId: string, prompt: string) => void;
};

export type DecisionFlowNode = Node<DecisionNodeData, "decision">;
export type DecisionFlowEdge = Edge;