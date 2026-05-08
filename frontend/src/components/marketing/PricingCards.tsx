import { Check, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router";
import { useAuth } from "@/hooks/useAuth";

const plans = [
  {
    name: "Daily",
    description: "Perfect for trying it out",
    price: "150",
    period: "day",
    features: [
      "All Ligue 1 predictions",
      "EV analysis per match",
      "Confidence scores",
      "Kelly % recommendations",
      "24-hour access",
    ],
    cta: "Get Daily Access",
    popular: false,
  },
  {
    name: "Weekly",
    description: "Best for regular bettors",
    price: "700",
    period: "week",
    features: [
      "All Ligue 1 predictions",
      "EV analysis per match",
      "Confidence scores",
      "Kelly % recommendations",
      "7-day access",
      "Priority support",
    ],
    cta: "Get Weekly Access",
    popular: true,
  },
  {
    name: "Monthly",
    description: "Maximum value for pros",
    price: "2,000",
    period: "month",
    features: [
      "All Ligue 1 predictions",
      "EV analysis per match",
      "Confidence scores",
      "Kelly % recommendations",
      "30-day access",
      "Priority support",
      "Historical data access",
    ],
    cta: "Get Monthly Access",
    popular: false,
  },
];

export function PricingCards() {
  const { isAuthenticated } = useAuth();

  return (
    <section className="relative py-24 bg-slate-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Simple, Transparent Pricing
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            No hidden fees. Cancel anytime. Pay with M-Pesa.
          </p>
        </div>
        
        <div className="grid gap-8 md:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border p-6 ${
                plan.popular
                  ? "border-accent-500/50 bg-slate-900/80 shadow-glow-gold"
                  : "border-slate-800 bg-slate-900/50"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center gap-1 rounded-full gradient-gold px-3 py-1 text-xs font-semibold text-slate-900">
                    <Sparkles className="h-3 w-3" />
                    Most Popular
                  </span>
                </div>
              )}
              
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
                <p className="text-sm text-slate-400 mt-1">{plan.description}</p>
              </div>
              
              <div className="mb-6">
                <span className="text-4xl font-bold text-white">KES {plan.price}</span>
                <span className="text-sm text-slate-400">/{plan.period}</span>
              </div>
              
              <ul className="mb-6 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm text-slate-300">
                    <Check className="h-4 w-4 text-success-500 mt-0.5 shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              
              <Link to={isAuthenticated ? "/subscription" : "/login"} className="block">
                <Button
                  className={`w-full ${
                    plan.popular
                      ? "gradient-gold text-slate-900 hover:opacity-90"
                      : "bg-primary-600 hover:bg-primary-500 text-white"
                  }`}
                >
                  {plan.cta}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
