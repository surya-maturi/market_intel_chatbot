import type { StepEvent, StepState } from "./types";

export function applyStepEvent(steps: StepState[], event: StepEvent): StepState[] {
  const next: StepState = {
    node: event.node,
    status: event.status,
    used_demo: event.used_demo ?? false,
    summary: event.summary ?? "",
  };
  const idx = steps.findIndex((s) => s.node === event.node);
  if (idx === -1) return [...steps, next];
  const updated = [...steps];
  updated[idx] = { ...updated[idx], ...next };
  return updated;
}
