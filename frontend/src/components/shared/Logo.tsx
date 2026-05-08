import { BrainCircuit } from "lucide-react";
import { Link } from "react-router";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <Link to="/" className={`flex items-center gap-2 ${className}`}>
      <div className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600">
        <BrainCircuit className="h-5 w-5 text-white" />
        <div className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-accent-500" />
      </div>
      <div className="flex flex-col">
        <span className="text-lg font-bold leading-tight tracking-tight text-white">
          Ligue 1
        </span>
        <span className="text-[10px] font-semibold leading-tight tracking-widest text-accent-400 uppercase">
          Predictor
        </span>
      </div>
    </Link>
  );
}
