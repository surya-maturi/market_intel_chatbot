"use client";

import { useCallback, useRef, useState } from "react";
import { fetchChatStream } from "../lib/api";
import { getStoredSessionId, setStoredSessionId } from "../lib/session";
import { applyStepEvent } from "../lib/streamReducer";
import type { ChatStreamEvent, ConversationTurn } from "../lib/types";

const NODE_LABELS: Record<string, string> = {
  classify_intent: "Detecting intent",
  fetch_reddit: "Fetching Reddit posts",
  analyze_sentiment: "Analyzing sentiment",
  synthesize: "Synthesizing insight",
  fetch_company: "Fetching company profile",
  clarify: "Preparing clarification",
};

export function nodeLabel(node: string): string {
  return NODE_LABELS[node] ?? node;
}

export function useChatStream() {
  const [sessionId, setSessionId] = useState<string | null>(() => getStoredSessionId());
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (message: string) => {
      const turnId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      setTurns((prev) => [
        ...prev,
        { id: turnId, userMessage: message, steps: [], result: null, errors: [], status: "streaming" },
      ]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      const updateTurn = (updater: (turn: ConversationTurn) => ConversationTurn) => {
        setTurns((prev) => prev.map((t) => (t.id === turnId ? updater(t) : t)));
      };

      try {
        await fetchChatStream(
          message,
          sessionId,
          (event: ChatStreamEvent) => {
            if (event.type === "session") {
              setSessionId(event.session_id);
              setStoredSessionId(event.session_id);
            } else if (event.type === "step") {
              updateTurn((turn) => ({ ...turn, steps: applyStepEvent(turn.steps, event) }));
            } else if (event.type === "error") {
              updateTurn((turn) => ({ ...turn, errors: [...turn.errors, event] }));
            } else if (event.type === "result") {
              updateTurn((turn) => ({ ...turn, result: event }));
            } else if (event.type === "done") {
              updateTurn((turn) => ({ ...turn, status: "done" }));
            }
          },
          controller.signal
        );
      } catch (err) {
        updateTurn((turn) => ({
          ...turn,
          status: "error",
          errorMessage: err instanceof Error ? err.message : "Something went wrong.",
        }));
      } finally {
        setIsStreaming(false);
      }
    },
    [sessionId]
  );

  return { turns, send, isStreaming, sessionId };
}
