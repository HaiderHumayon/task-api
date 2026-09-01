import { serve } from "inngest/next";

import { inngest } from "@/inngest/client";
import { executeDecisionFlow } from "@/inngest/functions/execute-decision-flow";

export const { GET, POST, PUT } = serve({
  client: inngest,
  functions: [
    executeDecisionFlow,
  ],
});