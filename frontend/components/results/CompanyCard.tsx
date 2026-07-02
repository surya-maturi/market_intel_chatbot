import type { CompanyPayload } from "../../lib/types";
import { Stat } from "./Stat";

interface CompanyCardProps {
  payload: CompanyPayload;
}

export function CompanyCard({ payload }: CompanyCardProps) {
  return (
    <div className="animate-fade-slide-in flex flex-col gap-3 rounded-xl border border-white/10 bg-white/[0.04] p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">{payload.name}</h3>
        <span className="rounded-full border border-white/20 bg-white/5 px-2 py-0.5 text-xs text-white/60">
          source: {payload.source}
        </span>
      </div>
      <p className="text-sm text-white/70">{payload.description ?? "No description available."}</p>
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Employees" value={payload.employees != null ? String(payload.employees) : "—"} />
        <Stat label="Est. revenue" value={payload.estimated_revenue ?? "—"} />
        <Stat label="Total funding" value={payload.total_funding ?? "—"} />
      </div>
    </div>
  );
}
