import OpenAI from "openai";
import { z } from "zod";

export const strictDecisionSchema =
  z.enum(["YES", "NO"]);

export type StrictDecision =
  z.infer<typeof strictDecisionSchema>;

export type LlmDecisionResult = {
  decision: StrictDecision;
  model: string;
};

function requireEnvironmentValue(
  name: string,
) {
  const value = process.env[name]?.trim();

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

function createOpenAIClient() {
  const apiKey =
    requireEnvironmentValue(
      "OPENAI_API_KEY",
    );

  const baseURL =
    process.env.OPENAI_BASE_URL?.trim();

  return new OpenAI({
    apiKey,
    ...(baseURL
      ? {
          baseURL,
        }
      : {}),
  });
}

export async function decideWithLlm(
  prompt: string,
): Promise<LlmDecisionResult> {
  const model =
    process.env.OPENAI_MODEL?.trim() ||
    "gpt-4o-mini";

  const client =
    createOpenAIClient();

  const completion =
    await client.chat.completions.create({
      model,
      temperature: 0,
      max_tokens: 3,
      messages: [
        {
          role: "system",
          content:
            "You are a binary decision engine. Answer the user's decision prompt with exactly one token: YES or NO. Do not explain, punctuate, qualify, or add any other text.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
    });

  const rawOutput =
    completion.choices[0]?.message.content;

  if (!rawOutput) {
    throw new Error(
      "LLM returned an empty decision.",
    );
  }

  return {
    decision:
      parseStrictDecision(rawOutput),
    model,
  };
}