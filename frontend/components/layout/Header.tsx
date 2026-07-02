"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "../../lib/api";
import type { HealthResponse, ServiceStatus } from "../../lib/types";

const STATUS_STYLES: Record<ServiceStatus, string> = {
  configured: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  demo: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  disabled: "bg-white/10 text-white/40 border-white/15",
};

export function Header() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <header className="flex h-16 items-center justify-between border-b border-white/10 px-6">
      <div>
        <h1 className="text-base font-semibold text-white">Market Intelligence Chatbot</h1>
        <p className="text-xs text-white/50">Trend · Sentiment · Competitor research for startup founders</p>
      </div>
      {health && (
        <div className="flex gap-2">
          {Object.entries(health.services).map(([name, status]) => (
            <span key={name} className={`rounded-full border px-2 py-0.5 text-xs capitalize ${STATUS_STYLES[status]}`}>
              {name}: {status}
            </span>
          ))}
        </div>
      )}
    </header>
  );
}
