import type { ConversationTurn } from "../../lib/types";
import { isCompanyPayload, isSynthesisPayload } from "../../lib/types";
import { CompanyCard } from "../results/CompanyCard";
import { SynthesisCard } from "../results/SynthesisCard";
import { AgentStepTimeline } from "./AgentStepTimeline";

interface MessageBubbleProps {
  turn: ConversationTurn;
}

export function MessageBubble({ turn }: MessageBubbleProps) {
  const payload = turn.result?.payload;

  return (
    <div className="flex flex-col gap-3">
      <div className="ml-auto max-w-xl rounded-2xl rounded-br-sm bg-sky-600 px-4 py-2 text-sm text-white">
        {turn.userMessage}
      </div>

      <div className="mr-auto flex w-full max-w-2xl flex-col gap-3">
        <AgentStepTimeline steps={turn.steps} />

        {turn.status === "error" && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm text-rose-300">
            {turn.errorMessage ?? "Something went wrong."}
          </div>
        )}

        {payload && isSynthesisPayload(payload) && <SynthesisCard payload={payload} />}
        {payload && isCompanyPayload(payload) && <CompanyCard payload={payload} />}
        {payload && !isSynthesisPayload(payload) && !isCompanyPayload(payload) && (
          <div className="animate-fade-slide-in whitespace-pre-line rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white/85">
            {"message" in payload ? payload.message : "No response."}
          </div>
        )}
      </div>
    </div>
  );
}
