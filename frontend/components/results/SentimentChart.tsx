"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SentimentResult } from "../../lib/types";

interface SentimentChartProps {
  sentiment: SentimentResult;
}

const BUCKET_COUNT = 10;

function buildHistogram(scores: number[]) {
  const buckets = Array.from({ length: BUCKET_COUNT }, (_, i) => {
    const start = -1 + (i * 2) / BUCKET_COUNT;
    return { label: start.toFixed(1), count: 0 };
  });
  for (const score of scores) {
    const idx = Math.min(BUCKET_COUNT - 1, Math.max(0, Math.floor(((score + 1) / 2) * BUCKET_COUNT)));
    buckets[idx].count += 1;
  }
  return buckets;
}

export function SentimentChart({ sentiment }: SentimentChartProps) {
  if (sentiment.raw_scores.length === 0) return null;
  const data = buildHistogram(sentiment.raw_scores);

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-2 flex items-center justify-between text-sm text-white/70">
        <span>Sentiment distribution ({sentiment.post_count} posts)</span>
        <span className="font-medium text-white/90">
          Weighted avg: {sentiment.weighted_avg.toFixed(2)} ({sentiment.label})
        </span>
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey="label" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} />
          <YAxis allowDecimals={false} tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#0b0f14", border: "1px solid rgba(255,255,255,0.1)" }}
            labelStyle={{ color: "white" }}
          />
          <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
