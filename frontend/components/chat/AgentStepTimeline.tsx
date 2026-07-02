import { nodeLabel } from "../../hooks/useChatStream";
import type { StepState } from "../../lib/types";
import { DemoDataBadge } from "./DemoDataBadge";

interface AgentStepTimelineProps {
  steps: StepState[];
}

function StepIcon({ status }: { status: StepState["status"] }) {
  if (status === "completed") {
    return (
      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
        ✓
      </span>
    );
  }
  return (
    <span className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-sky-400/60 border-t-transparent animate-spin" />
  );
}

export function AgentStepTimeline({ steps }: AgentStepTimelineProps) {
  if (steps.length === 0) return null;

  return (
    <ol className="flex flex-col gap-2 rounded-lg border border-white/10 bg-white/[0.03] p-3">
      {steps.map((step) => (
        <li key={step.node} className="flex items-center gap-3 text-sm">
          <StepIcon status={step.status} />
          <span className={step.status === "completed" ? "text-white/90" : "text-white/50 animate-pulse-soft"}>
            {step.summary || nodeLabel(step.node)}
          </span>
          {step.status === "completed" && step.used_demo && <DemoDataBadge />}
        </li>
      ))}
    </ol>
  );
}
