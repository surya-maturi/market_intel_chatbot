import { describe, expect, it } from "vitest";
import { parseSSEBlock, resolveApiBaseUrl } from "./api";

describe("resolveApiBaseUrl", () => {
  it("defaults to localhost:8000 when unset (local dev)", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("http://localhost:8000");
  });

  it("resolves to an empty string for the same-origin single-project setup", () => {
    expect(resolveApiBaseUrl("same-origin")).toBe("");
  });

  it("passes through an explicit absolute URL unchanged", () => {
    expect(resolveApiBaseUrl("https://my-backend.onrender.com")).toBe("https://my-backend.onrender.com");
  });
});

describe("parseSSEBlock", () => {
  it("parses a single data line into one event", () => {
    const events = parseSSEBlock('data: {"type": "done"}');
    expect(events).toEqual([{ type: "done" }]);
  });

  it("parses a step event with all fields", () => {
    const events = parseSSEBlock(
      'data: {"type": "step", "node": "classify_intent", "status": "completed", "used_demo": true, "summary": "Detected intent: trend"}'
    );
    expect(events).toHaveLength(1);
    expect(events[0]).toMatchObject({ type: "step", node: "classify_intent", used_demo: true });
  });

  it("ignores non-data lines", () => {
    const events = parseSSEBlock(': this is a comment\ndata: {"type": "done"}');
    expect(events).toEqual([{ type: "done" }]);
  });

  it("returns multiple events when a block has multiple data lines", () => {
    const events = parseSSEBlock('data: {"type": "done"}\ndata: {"type": "session", "session_id": "abc"}');
    expect(events).toHaveLength(2);
  });
});
