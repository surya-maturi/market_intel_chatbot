"use client";

import { useEffect, useRef } from "react";
import { useChatStream } from "../../hooks/useChatStream";
import { ChatInput } from "./ChatInput";
import { MessageBubble } from "./MessageBubble";

const SUGGESTIONS = [
  "Is remote work becoming more popular?",
  "What do people think about Notion's pricing?",
  "Tell me about Figma as a company",
];

export function ChatWindow() {
  const { turns, send, isStreaming } = useChatStream();
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  return (
    <div className="flex h-[calc(100vh-64px)] flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {turns.length === 0 && (
          <div className="mx-auto max-w-xl text-center text-white/60">
            <p className="mb-4">Ask about market trends, sentiment, or a competitor.</p>
            <div className="flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-white/80 transition hover:bg-white/[0.07]"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mx-auto flex max-w-3xl flex-col gap-6">
          {turns.map((turn) => (
            <MessageBubble key={turn.id} turn={turn} />
          ))}
        </div>
        <div ref={bottomRef} />
      </div>

      <div className="mx-auto w-full max-w-3xl">
        <ChatInput onSend={send} disabled={isStreaming} />
      </div>
    </div>
  );
}
