import type { ChatHistoryResponse, ChatStreamEvent, HealthResponse } from "./types";

// Nullish coalescing, not ||: an explicitly empty string means "same origin, no
// base URL" (used when frontend and backend are rewritten under one Vercel domain).
// Only a genuinely unset env var should fall back to the local dev default.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
