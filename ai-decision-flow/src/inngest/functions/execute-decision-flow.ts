import {
  decisionFlowExecute,
  inngest,
  type DecisionFlowEventData,
} from "@/inngest/client";
import {
  decideWithLlm,
  type StrictDecision,
} from "@/lib/decision-engine";

type ExecutionResult = {
  nodeId: string;
  title: string;
  prompt: string;
  decision: StrictDecision;
  model: string;
};

function getNextEdge(
  edges: DecisionFlowEventData["edges"],
  nodeId: string,
  decision: StrictDecision,
) {
  return edges.find(
    (edge) =>
      edge.source === nodeId &&
      edge.branch === decision,
  );
}

export const executeDecisionFlow =
  inngest.createFunction(
    {
      id: "execute-decision-flow",
      name: "Execute AI Decision Flow",
      triggers: [decisionFlowExecute],
      retries: 2,
    },
    async ({
      event,
      step,
      logger,
    }) => {
      const {
        nodes,
        edges,
        startNodeId,
      } = event.data;

      const nodesById = new Map(
        nodes.map((node) => [
          node.id,
          node,
        ]),
      );

      const visited = new Set<string>();
      const executionOrder: string[] = [];
      const results: ExecutionResult[] = [];

      let currentNodeId = startNodeId;

      for (
        let stepIndex = 0;
        stepIndex < nodes.length;
        stepIndex += 1
      ) {
        if (visited.has(currentNodeId)) {
          throw new Error(
            `Cycle detected at ${currentNodeId}.`,
          );
        }

        const node =
          nodesById.get(currentNodeId);

        if (!node) {
          throw new Error(
            `Node ${currentNodeId} does not exist.`,
          );
        }

        visited.add(currentNodeId);

        const result = await step.run(
          `node-${stepIndex + 1}-${currentNodeId}`,
          async () => {
            const llmResult =
              await decideWithLlm(
                node.prompt,
              );

            logger.info(
              {
                nodeId:
                  currentNodeId,
                decision:
                  llmResult.decision,
                model:
                  llmResult.model,
              },
              "AI decision node executed",
            );

            return {
              nodeId:
                currentNodeId,
              title: node.title,
              prompt: node.prompt,
              decision:
                llmResult.decision,
              model:
                llmResult.model,
            } satisfies ExecutionResult;
          },
        );

        executionOrder.push(
          currentNodeId,
        );
        results.push(result);

        const nextEdge = getNextEdge(
          edges,
          currentNodeId,
          result.decision,
        );

        if (!nextEdge) {
          return {
            status: "completed",
            terminalNodeId:
              currentNodeId,
            executionOrder,
            results,
          };
        }

        currentNodeId =
          nextEdge.target;
      }

      throw new Error(
        "Traversal exceeded the number of graph nodes.",
      );
    },
  );