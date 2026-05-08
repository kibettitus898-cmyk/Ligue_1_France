import { cn } from "@/lib/utils";

interface ConfidenceMeterProps {
  value: number;
  className?: string;
}

export function ConfidenceMeter({ value, className }: ConfidenceMeterProps) {
  const percentage = Math.min(100, Math.max(0, value));
  let color = "bg-slate-600";
  if (percentage >= 75) color = "bg-success-500";
  else if (percentage >= 50) color = "bg-primary-500";
  else if (percentage >= 25) color = "bg-accent-500";
  else color = "bg-danger-500";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-2 flex-1 rounded-full bg-slate-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-medium text-slate-300 w-8 text-right">
        {percentage}%
      </span>
    </div>
  );
}
