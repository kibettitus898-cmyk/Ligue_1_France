import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router";

export function CTA() {
  return (
    <section className="relative py-24">
      <div className="absolute inset-0 gradient-hero" />
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-5" />
      
      <div className="relative mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Stop Gambling. Start Investing.
        </h2>
        <p className="mt-4 text-lg text-slate-300">
          Join the community of data-driven bettors who treat every wager as a calculated investment.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link to="/dashboard">
            <Button size="lg" className="gap-2 bg-accent-500 hover:bg-accent-400 text-slate-900 font-semibold px-8">
              Start Predicting
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
        <p className="mt-4 text-xs text-slate-500">
          No credit card required. Pay with M-Pesa.
        </p>
      </div>
    </section>
  );
}
