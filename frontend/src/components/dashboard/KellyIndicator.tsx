import { cn } from "@/lib/utils";

interface KellyIndicatorProps {
  fraction: number;
  className?: string;
}

export function KellyIndicator({ fraction, className }: KellyIndicatorProps) {
  const safeFraction = Math.max(0, Math.min(100, fraction));
  const quarterKelly = (safeFraction / 4).toFixed(1);

  let colorClass = "text-slate-400";
  if (safeFraction > 5) colorClass = "text-success-500";
  else if (safeFraction > 2) colorClass = "text-primary-400";
  else if (safeFraction > 0) colorClass = "text-accent-400";

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className="flex items-baseline gap-1">
        <span className="text-xs text-slate-500">Kelly</span>
        <span className={`text-sm font-bold ${colorClass}`}>{safeFraction.toFixed(1)}%</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-xs text-slate-500">1/4 Kelly</span>
        <span className={`text-xs font-semibold ${colorClass}`}>{quarterKelly}%</span>
      </div>
    </div>
  );
}
