import { Smartphone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface MPesaButtonProps {
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
  className?: string;
  children?: React.ReactNode;
  variant?: "default" | "outline" | "gold";
}

export function MPesaButton({
  onClick,
  loading,
  disabled,
  className,
  children,
  variant = "default",
}: MPesaButtonProps) {
  const baseStyles = "relative flex items-center gap-2 font-semibold";
  
  const variants = {
    default: "bg-success-600 hover:bg-success-500 text-white",
    outline: "border-success-500 text-success-500 hover:bg-success-500/10",
    gold: "gradient-gold text-slate-900 hover:opacity-90",
  };

  return (
    <Button
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(baseStyles, variants[variant], className)}
    >
      {loading ? (
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        <Smartphone className="h-4 w-4" />
      )}
      {children || "Pay with M-Pesa"}
    </Button>
  );
}
