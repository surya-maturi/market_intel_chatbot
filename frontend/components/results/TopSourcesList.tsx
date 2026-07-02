import type { SourceCitation } from "../../lib/types";

const SENTIMENT_COLORS: Record<SourceCitation["sentiment"], string> = {
  positive: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  negative: "bg-rose-500/20 text-rose-300 border-rose-500/40",
  neutral: "bg-white/10 text-white/60 border-white/20",
};

interface TopSourcesListProps {
  sources: SourceCitation[];
}

export function TopSourcesList({ sources }: TopSourcesListProps) {
  if (sources.length === 0) return null;

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-2 text-sm text-white/70">Top sources</div>
      <ul className="flex flex-col gap-2">
        {sources.map((source) => (
          <li key={source.url || source.title} className="flex items-start gap-2 text-sm">
            <span
              className={`shrink-0 rounded-full border px-2 py-0.5 text-xs ${SENTIMENT_COLORS[source.sentiment]}`}
            >
              {source.sentiment}
            </span>
            {source.url ? (
              <a href={source.url} target="_blank" rel="noreferrer" className="text-sky-300 hover:underline">
                {source.title}
              </a>
            ) : (
              <span className="text-white/80">{source.title}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
