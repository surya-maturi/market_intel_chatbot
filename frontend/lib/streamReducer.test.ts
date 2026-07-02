import { describe, expect, it } from "vitest";
import { applyStepEvent } from "./streamReducer";
import type { StepEvent } from "./types";

describe("applyStepEvent", () => {
  it("adds a new step when the node hasn't been seen before", () => {
    const started: StepEvent = { type: "step", node: "classify_intent", status: "started" };
    const result = applyStepEvent([], started);
    expect(result).toEqual([{ node: "classify_intent", status: "started", used_demo: false, summary: "" }]);
  });

  it("updates the existing step in place when the same node completes", () => {
    const started: StepEvent = { type: "step", node: "classify_intent", status: "started" };
    const completed: StepEvent = {
      type: "step",
      node: "classify_intent",
      status: "completed",
      used_demo: true,
      summary: "Detected intent: trend",
    };
    const afterStart = applyStepEvent([], started);
    const afterComplete = applyStepEvent(afterStart, completed);

    expect(afterComplete).toHaveLength(1);
    expect(afterComplete[0]).toEqual({
      node: "classify_intent",
      status: "completed",
      used_demo: true,
      summary: "Detected intent: trend",
    });
  });

  it("preserves order across multiple distinct nodes", () => {
    const afterIntent = applyStepEvent([], { type: "step", node: "classify_intent", status: "started" });
    const afterReddit = applyStepEvent(afterIntent, { type: "step", node: "fetch_reddit", status: "started" });
    expect(afterReddit.map((s) => s.node)).toEqual(["classify_intent", "fetch_reddit"]);
  });
});
