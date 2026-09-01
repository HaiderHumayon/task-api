import { Inngest } from "inngest";

const isDev =
  process.env.INNGEST_DEV === "1" ||
  process.env.NODE_ENV === "development";

export const inngest = new Inngest({
  id: "ai-decision-flow",
  isDev,
});