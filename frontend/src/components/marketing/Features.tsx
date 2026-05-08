import { Brain, BarChart3, Smartphone, Clock, ShieldCheck, TrendingUp } from "lucide-react";

const features = [
  {
    name: "AI Model Ensemble",
    description: "Combines XGBoost, Random Forest, and neural networks trained on 5+ seasons of Ligue 1 data.",
    icon: Brain,
    color: "text-primary-400",
    bg: "bg-primary-500/10",
  },
  {
    name: "Expected Value (EV) Analysis",
    description: "Every prediction includes EV calculation so you only bet when the odds are in your favor.",
    icon: BarChart3,
    color: "text-success-400",
    bg: "bg-success-500/10",
  },
  {
    name: "M-Pesa Integration",
    description: "Seamless payments via M-Pesa. No cards needed. Subscribe in seconds from your phone.",
    icon: Smartphone,
    color: "text-accent-400",
    bg: "bg-accent-500/10",
  },
  {
    name: "Real-Time Updates",
    description: "Predictions refresh automatically as new fixtures and odds data become available.",
    icon: Clock,
    color: "text-primary-400",
    bg: "bg-primary-500/10",
  },
  {
    name: "Bankroll Management",
    description: "Kelly Criterion percentages help you size bets proportionally to your edge and bankroll.",
    icon: ShieldCheck,
    color: "text-success-400",
    bg: "bg-success-500/10",
  },
  {
    name: "Historical Performance",
    description: "Track model accuracy over time. Full transparency on win rates and ROI by bet type.",
    icon: TrendingUp,
    color: "text-accent-400",
    bg: "bg-accent-500/10",
  },
];

export function Features() {
  return (
    <section className="relative py-24 bg-slate-950">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Built for Serious Bettors
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            Every feature is designed to give you an analytical edge over casual punters and bookmakers.
          </p>
        </div>
        
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.name}
              className="relative rounded-2xl border border-slate-800 bg-slate-900/50 p-6 hover:border-slate-700 transition-colors"
            >
              <div className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${feature.bg} ${feature.color} mb-4`}>
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.name}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
