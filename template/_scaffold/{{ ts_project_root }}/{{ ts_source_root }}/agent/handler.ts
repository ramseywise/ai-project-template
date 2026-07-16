/**
 * Framework-agnostic chat endpoint — a plain (req: Request) => Response
 * function, not tied to Express or Next.js. Wire it into Express today
 * (see ../app.ts.jinja's POST /agent/chat route) or drop it straight into a
 * Next.js App Router route handler (`export const POST = chatHandler;`) in a
 * Vercel-hosted project — same function either way.
 */

import type { UIMessage } from "ai";
import { runAgent } from "./agent.js";

export async function chatHandler(req: Request): Promise<Response> {
  const body = (await req.json()) as { messages?: UIMessage[] };
  if (!Array.isArray(body.messages)) {
    return Response.json({ error: "messages must be an array" }, { status: 400 });
  }

  const result = runAgent(body.messages);
  return result.toUIMessageStreamResponse();
}
