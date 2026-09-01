import type {
  BranchType,
  DecisionFlowEdge,
  DecisionFlowNode,
} from "@/components/decision-flow/types";

export const GRAPH_STORAGE_KEY =
  "ai-decision-flow:graph:v1";

export type PortableNode = {
  id: string;
  type: "decision";
  position: {
    x: number;
    y: number;
  };
  data: {
    title: string;
    prompt: string;
  };
};

export type PortableEdge = {
  id: string;
  source: string;
  target: string;
  sourceHandle:
    | "yes"
    | "no";
  targetHandle: "input";
  branch: BranchType;
};

export type PortableGraph = {
  version: 1;
  savedAt: string;
  nodes: PortableNode[];
  edges: PortableEdge[];
};

function isRecord(
  value: unknown,
): value is Record<
  string,
  unknown
> {
  return (
    typeof value ===
      "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function isFiniteNumber(
  value: unknown,
): value is number {
  return (
    typeof value ===
      "number" &&
    Number.isFinite(value)
  );
}

function isBranch(
  value: unknown,
): value is BranchType {
  return (
    value === "YES" ||
    value === "NO"
  );
}

export function serializeGraph(
  nodes: DecisionFlowNode[],
  edges: DecisionFlowEdge[],
): PortableGraph {
  return {
    version: 1,
    savedAt:
      new Date().toISOString(),
    nodes: nodes.map(
      (node) => ({
        id: node.id,
        type: "decision",
        position: {
          x: node.position.x,
          y: node.position.y,
        },
        data: {
          title:
            node.data.title,
          prompt:
            node.data.prompt,
        },
      }),
    ),
    edges: edges
      .filter(
        (edge) =>
          edge.data?.branch,
      )
      .map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle:
          edge.data?.branch ===
          "YES"
            ? "yes"
            : "no",
        targetHandle:
          "input",
        branch:
          edge.data!.branch,
      })),
  };
}

export function parsePortableGraph(
  input: unknown,
): PortableGraph {
  if (!isRecord(input)) {
    throw new Error(
      "Workflow JSON must contain an object.",
    );
  }

  if (input.version !== 1) {
    throw new Error(
      "Unsupported workflow JSON version.",
    );
  }

  if (
    !Array.isArray(
      input.nodes,
    ) ||
    !Array.isArray(
      input.edges,
    )
  ) {
    throw new Error(
      "Workflow JSON must include nodes and edges arrays.",
    );
  }

  const nodeIds =
    new Set<string>();

  const nodes: PortableNode[] =
    input.nodes.map(
      (
        candidate,
        index,
      ) => {
        if (
          !isRecord(candidate) ||
          typeof candidate.id !==
            "string" ||
          candidate.type !==
            "decision" ||
          !isRecord(
            candidate.position,
          ) ||
          !isFiniteNumber(
            candidate.position.x,
          ) ||
          !isFiniteNumber(
            candidate.position.y,
          ) ||
          !isRecord(
            candidate.data,
          ) ||
          typeof candidate.data
            .title !== "string" ||
          typeof candidate.data
            .prompt !== "string"
        ) {
          throw new Error(
            `Invalid node at index ${index}.`,
          );
        }

        if (
          !candidate.id.trim()
        ) {
          throw new Error(
            `Node ${index} has an empty ID.`,
          );
        }

        if (
          nodeIds.has(
            candidate.id,
          )
        ) {
          throw new Error(
            `Duplicate node ID: ${candidate.id}.`,
          );
        }

        nodeIds.add(
          candidate.id,
        );

        return {
          id: candidate.id,
          type: "decision",
          position: {
            x:
              candidate.position.x,
            y:
              candidate.position.y,
          },
          data: {
            title:
              candidate.data.title,
            prompt:
              candidate.data.prompt,
          },
        };
      },
    );

  if (nodes.length === 0) {
    throw new Error(
      "Workflow must contain at least one node.",
    );
  }

  const branchKeys =
    new Set<string>();

  const edges: PortableEdge[] =
    input.edges.map(
      (
        candidate,
        index,
      ) => {
        if (
          !isRecord(candidate) ||
          typeof candidate.id !==
            "string" ||
          typeof candidate.source !==
            "string" ||
          typeof candidate.target !==
            "string" ||
          !isBranch(
            candidate.branch,
          )
        ) {
          throw new Error(
            `Invalid edge at index ${index}.`,
          );
        }

        if (
          !nodeIds.has(
            candidate.source,
          ) ||
          !nodeIds.has(
            candidate.target,
          )
        ) {
          throw new Error(
            `Edge ${candidate.id} references a missing node.`,
          );
        }

        if (
          candidate.source ===
          candidate.target
        ) {
          throw new Error(
            `Edge ${candidate.id} creates a self-loop.`,
          );
        }

        const branchKey =
          `${candidate.source}:${candidate.branch}`;

        if (
          branchKeys.has(
            branchKey,
          )
        ) {
          throw new Error(
            `${candidate.source} has more than one ${candidate.branch} branch.`,
          );
        }

        branchKeys.add(
          branchKey,
        );

        return {
          id: candidate.id,
          source:
            candidate.source,
          target:
            candidate.target,
          sourceHandle:
            candidate.branch ===
            "YES"
              ? "yes"
              : "no",
          targetHandle:
            "input",
          branch:
            candidate.branch,
        };
      },
    );

  return {
    version: 1,
    savedAt:
      typeof input.savedAt ===
        "string"
        ? input.savedAt
        : new Date().toISOString(),
    nodes,
    edges,
  };
}