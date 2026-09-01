import { NextResponse } from "next/server";

import {
  decisionFlowEventDataSchema,
  decisionFlowExecute,
  inngest,
  type DecisionFlowEventData,
} from "@/inngest/client";

function validateGraph(
  data: DecisionFlowEventData,
) {
  const nodeIds = new Set(
    data.nodes.map((node) => node.id),
  );

  if (
    nodeIds.size !==
    data.nodes.length
  ) {
    return "Node IDs must be unique.";
  }

  if (
    !nodeIds.has(data.startNodeId)
  ) {
    return "Start node does not exist.";
  }

  const branchKeys = new Set<string>();

  for (const edge of data.edges) {
    if (
      !nodeIds.has(edge.source) ||
      !nodeIds.has(edge.target)
    ) {
      return `Edge ${edge.id} references a missing node.`;
    }

    if (edge.source === edge.target) {
      return `Edge ${edge.id} creates a self-loop.`;
    }

    const branchKey =
      `${edge.source}:${edge.branch}`;

    if (branchKeys.has(branchKey)) {
      return `${edge.source} has more than one ${edge.branch} branch.`;
    }

    branchKeys.add(branchKey);
  }

  return null;
}

export async function POST(
  request: Request,
) {
  let body: unknown;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      {
        error:
          "Request body must be valid JSON.",
      },
      {
        status: 400,
      },
    );
  }

  const parsed =
    decisionFlowEventDataSchema.safeParse(
      body,
    );

  if (!parsed.success) {
    return NextResponse.json(
      {
        error:
          "Invalid decision-flow payload.",
        details:
          parsed.error.flatten(),
      },
      {
        status: 400,
      },
    );
  }

  const graphError =
    validateGraph(parsed.data);

  if (graphError) {
    return NextResponse.json(
      {
        error: graphError,
      },
      {
        status: 400,
      },
    );
  }

  const sent = await inngest.send(
    decisionFlowExecute.create(
      parsed.data,
    ),
  );

  return NextResponse.json(
    {
      accepted: true,
      eventId:
        sent.ids[0] ?? null,
      startNodeId:
        parsed.data.startNodeId,
      nodeCount:
        parsed.data.nodes.length,
      edgeCount:
        parsed.data.edges.length,
      executionMode: "llm",
    },
    {
      status: 202,
    },
  );
}