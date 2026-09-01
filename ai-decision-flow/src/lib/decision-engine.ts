import OpenAI from "openai";
import { z } from "zod";

export const strictDecisionSchema =
  z.enum(["YES", "NO"]);

export type StrictDecision =
  z.infer<
    typeof strictDecisionSchema
  >;

export type LlmDecisionResult = {
  decision: StrictDecision;
  model: string;
};

function requireEnvironmentValue(
  name: string,
) {
  const value =
    process.env[name]?.trim();

  if (!value) {
    throw new Error(
      `${name} is required to execute AI decision nodes.`,
    );
  }

  return value;
}

export function parseStrictDecision(
  rawOutput: string,
): StrictDecision {
  const normalized =
    rawOutput.trim().toUpperCase();

  const parsed =
    strictDecisionSchema.safeParse(
      normalized,
    );

  if (!parsed.success) {
    throw new Error(
      `LLM must return exactly YES or NO. Received: ${JSON.stringify(rawOutput)}`,
    );
  }

  return parsed.data;
}

function getConfiguration() {
  const apiKey =
    requireEnvironmentValue(
      "OPENAI_API_KEY",
    );

  const baseURL =
    process.env.OPENAI_BASE_URL?.trim();

  const model =
    process.env.OPENAI_MODEL?.trim() ||
    "gpt-4o-mini";

  return {
    apiKey,
    baseURL,
    model,
  };
}

export async function decideWithLlm(
  prompt: string,
): Promise<LlmDecisionResult> {
  const {
    apiKey,
    baseURL,
    model,
  } = getConfiguration();

  const client =
    new OpenAI({
      apiKey,
      ...(baseURL
        ? {
            baseURL,
          }
        : {}),
    });

  const completion =
    await client.chat.completions.create({
      model,
      temperature: 0,
      max_completion_tokens: 1024,
      messages: [
        {
          role: "user",
          content: [
            "Act as a binary decision engine.",
            "Answer the decision prompt with exactly YES or NO.",
            "Do not explain, punctuate, qualify, or add any other text.",
            "",
            "Decision prompt:",
            prompt,
          ].join("\n"),
        },
      ],
    });

  const choice =
    completion.choices[0];

  const rawOutput =
    choice?.message.content?.trim();

  if (!rawOutput) {
    throw new Error(
      `LLM returned an empty final decision. Finish reason: ${choice?.finish_reason ?? "unknown"}.`,
    );
  }

  return {
    decision:
      parseStrictDecision(
        rawOutput,
      ),
    model,
  };
}