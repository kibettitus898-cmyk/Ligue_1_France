import { Inbox } from "lucide-react";

export function EmptyState({ 
  message = "No data found", 
  submessage 
}: { 
  message?: string; 
  submessage?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
        <Inbox className="h-6 w-6 text-muted-foreground" />
      </div>
      <p className="text-sm font-medium text-muted-foreground">{message}</p>
      {submessage && (
        <p className="text-xs text-muted-foreground/60">{submessage}</p>
      )}
    </div>
  );
}
