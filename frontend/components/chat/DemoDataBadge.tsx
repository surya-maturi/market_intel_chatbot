interface DemoDataBadgeProps {
  reason?: string;
}

export function DemoDataBadge({ reason }: DemoDataBadgeProps) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-300"
      title={reason ?? "This section used sample data because the live API was unavailable."}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
      Demo data
    </span>
  );
}
