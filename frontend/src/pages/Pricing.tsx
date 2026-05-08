import { PricingCards } from "@/components/marketing/PricingCards";
import { Footer } from "@/components/marketing/Footer";
import { MarketingNav } from "@/components/marketing/MarketingNav";
import { ShieldCheck, RefreshCw, HelpCircle } from "lucide-react";

export default function Pricing() {
  return (
    <div className="min-h-screen bg-slate-950">
      <MarketingNav />
      <main className="pt-16">
        <div className="relative py-16">
          <div className="absolute inset-0 gradient-hero opacity-50" />
          <div className="relative mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Simple Pricing
            </h1>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              Choose the plan that fits your betting schedule. All plans include full access to predictions and EV analysis.
            </p>
          </div>
        </div>
        
        <PricingCards />
        
        <section className="py-24 bg-slate-950">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid gap-8 md:grid-cols-3">
              <div className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-success-500/10 mb-4">
                  <ShieldCheck className="h-6 w-6 text-success-500" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Secure Payments</h3>
                <p className="text-sm text-slate-400">
                  All payments processed securely via M-Pesa. Your financial data is never stored.
                </p>
              </div>
              
              <div className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-500/10 mb-4">
                  <RefreshCw className="h-6 w-6 text-primary-500" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Cancel Anytime</h3>
                <p className="text-sm text-slate-400">
                  No long-term contracts. Your subscription runs for the period you paid for and expires automatically.
                </p>
              </div>
              
              <div className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent-500/10 mb-4">
                  <HelpCircle className="h-6 w-6 text-accent-500" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">24/7 Support</h3>
                <p className="text-sm text-slate-400">
                  Get help whenever you need it. Weekly and monthly subscribers get priority response.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
