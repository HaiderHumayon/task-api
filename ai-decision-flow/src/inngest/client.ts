import { eventType, Inngest } from "inngest";
import { z } from "zod";

const isDev =
  process.env.INNGEST_DEV === "1" ||
  process.env.NODE_ENV === "development";

export const branchSchema =
  z.enum(["YES", "NO"]);

export const decisionFlowEventDataSchema =
  z.object({
    nodes: z
      .array(
        z.object({
          id: z.string().min(1),
          title: z.string().min(1),
          prompt: z.string().min(1),
        }),
      )
      .min(1),
    edges: z.array(
      z.object({
        id: z.string().min(1),
        source: z.string().min(1),
        target: z.string().min(1),
        branch: branchSchema,
      }),
    ),
    startNodeId: z.string().min(1),
  });

export type DecisionFlowEventData =
  z.infer<
    typeof decisionFlowEventDataSchema
  >;

export const decisionFlowExecute =
  eventType(
    "decision-flow/execute",
    {
      schema:
        decisionFlowEventDataSchema,
    },
  );

export const inngest = new Inngest({
  id: "ai-decision-flow",
  isDev,
});