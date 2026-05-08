import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ErrorState({ 
  message = "Something went wrong", 
  retry 
}: { 
  message?: string; 
  retry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-danger-500/10">
        <AlertTriangle className="h-6 w-6 text-danger-500" />
      </div>
      <p className="text-sm text-muted-foreground">{message}</p>
      {retry && (
        <Button variant="outline" size="sm" onClick={retry}>
          Try Again
        </Button>
      )}
    </div>
  );
}
