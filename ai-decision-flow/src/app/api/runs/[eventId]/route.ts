import { NextResponse } from "next/server";

import { getRun } from "@/lib/run-store";

export async function GET(
  _request: Request,
  context: {
    params: Promise<{
      eventId: string;
    }>;
  },
) {
  const { eventId } =
    await context.params;

  const run = getRun(eventId);

  if (!run) {
    return NextResponse.json(
      {
        error:
          "Execution state not found.",
      },
      {
        status: 404,
      },
    );
  }

  return NextResponse.json(run);
}