import type { SynthesisPayload } from "../../lib/types";
import { SentimentChart } from "./SentimentChart";
import { Stat } from "./Stat";
import { TopSourcesList } from "./TopSourcesList";

interface SynthesisCardProps {
  payload: SynthesisPayload;
}

export function SynthesisCard({ payload }: SynthesisCardProps) {
  return (
    <div className="animate-fade-slide-in flex flex-col gap-4 rounded-xl border border-white/10 bg-white/[0.04] p-5">
      <div>
        <h3 className="text-lg font-semibold text-white">{payload.headline}</h3>
        <p className="mt-1 text-sm text-white/70">{payload.summary}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Posts" value={String(payload.key_stats.post_count)} />
        <Stat label="Avg sentiment" value={payload.key_stats.avg_sentiment.toFixed(2)} />
        <Stat label="Positive" value={`${payload.key_stats.positive_pct}%`} />
        <Stat label="Negative" value={`${payload.key_stats.negative_pct}%`} />
      </div>

      {payload.sentiment && payload.sentiment.raw_scores.length > 0 && (
        <SentimentChart sentiment={payload.sentiment} />
      )}

      <div>
        <div className="mb-2 text-sm text-white/70">Recommendations</div>
        <ul className="list-disc space-y-1 pl-5 text-sm text-white/85">
          {payload.recommendations.map((rec, i) => (
            <li key={i}>{rec}</li>
          ))}
        </ul>
      </div>

      <TopSourcesList sources={payload.sources} />
    </div>
  );
}
