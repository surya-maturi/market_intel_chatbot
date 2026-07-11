import type { ChatHistoryResponse, ChatStreamEvent, HealthResponse } from "./types";

// "same-origin" is an explicit, unambiguous opt-in for the single-Vercel-project setup
// (frontend + backend rewritten under one domain via the root vercel.json) - relying on
// an empty string here instead would depend on whether the hosting UI even preserves a
// blank environment variable value, which isn't guaranteed. An unset var still falls
// back to the local dev default.
export function resolveApiBaseUrl(raw: string | undefined): string {
  if (raw === undefined) return "http://localhost:8000";
  if (raw === "same-origin") return "";
  return raw;
}

const API_BASE_URL = resolveApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);

export function parseSSEBlock(rawEvent: string): ChatStreamEvent[] {
  const events: ChatStreamEvent[] = [];
  for (const line of rawEvent.split("\n")) {
    if (line.startsWith("data: ")) {
      events.push(JSON.parse(line.slice("data: ".length)) as ChatStreamEvent);
    }
  }
  return events;
}

export async function fetchChatStream(
  message: string,
  sessionId: string | null,
  onEvent: (event: ChatStreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat stream request failed: ${response.status}`);
  }

  // Plain fetch + ReadableStream, not EventSource: EventSource only supports
  // GET, and this endpoint needs a POST body for the chat message.
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      for (const event of parseSSEBlock(rawEvent)) onEvent(event);
      boundary = buffer.indexOf("\n\n");
    }
  }
}

export async function fetchHistory(sessionId: string): Promise<ChatHistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/sessions/${sessionId}/history`);
  if (!response.ok) throw new Error(`Failed to fetch history: ${response.status}`);
  return response.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) throw new Error(`Failed to fetch health: ${response.status}`);
  return response.json();
}
