import { Search, LineChart, Wallet } from "lucide-react";

const steps = [
  {
    step: "01",
    title: "Choose Your Plan",
    description: "Subscribe via M-Pesa in seconds. Daily, weekly, or monthly access.",
    icon: Wallet,
  },
  {
    step: "02",
    title: "Get AI Predictions",
    description: "Our ensemble model analyzes fixtures and generates probabilities with confidence scores.",
    icon: Search,
  },
  {
    step: "03",
    title: "Bet with Edge",
    description: "Only place bets with positive EV. Use Kelly % for optimal bankroll sizing.",
    icon: LineChart,
  },
];

export function HowItWorks() {
  return (
    <section className="relative py-24 bg-slate-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            How It Works
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            From subscription to value bet in under 2 minutes.
          </p>
        </div>
        
        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((item, idx) => (
            <div key={item.step} className="relative">
              {idx < steps.length - 1 && (
                <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-px bg-gradient-to-r from-primary-500/50 to-transparent" />
              )}
              
              <div className="relative flex flex-col items-center text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-600/20 border border-primary-500/30 mb-6">
                  <item.icon className="h-7 w-7 text-primary-400" />
                </div>
                <span className="text-xs font-bold tracking-widest text-accent-400 uppercase mb-2">
                  Step {item.step}
                </span>
                <h3 className="text-xl font-semibold text-white mb-3">{item.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed max-w-xs">{item.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
