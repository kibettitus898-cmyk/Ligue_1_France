import { cn } from "@/lib/utils";

interface EVBadgeProps {
  ev: number;
  className?: string;
}

export function EVBadge({ ev, className }: EVBadgeProps) {
  const isPositive = ev > 0;
  const isHigh = Math.abs(ev) > 5;

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        isPositive
          ? isHigh
            ? "bg-success-500/20 text-success-500 ring-1 ring-success-500/30"
            : "bg-success-500/10 text-success-500"
          : "bg-danger-500/10 text-danger-500",
        className
      )}
    >
      {isPositive ? "+" : ""}
      {ev.toFixed(1)}% EV
    </span>
  );
}
