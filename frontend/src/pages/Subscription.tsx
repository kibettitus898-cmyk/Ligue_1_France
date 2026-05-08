import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { usePayment } from "@/hooks/usePayment";
import { useSubscription } from "@/hooks/useSubscription";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { MPesaButton } from "@/components/shared/MPesaButton";
import { Check, Clock, AlertTriangle, Sparkles, Calendar, Wallet, Zap } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const plans = [
  {
    name: "Daily",
    plan: "daily" as const,
    price: "150",
    duration: "24 hours",
    features: ["All predictions", "EV analysis", "Kelly %"],
    icon: Zap,
  },
  {
    name: "Weekly",
    plan: "weekly" as const,
    price: "700",
    duration: "7 days",
    features: ["All predictions", "EV analysis", "Kelly %", "Priority support"],
    icon: Calendar,
    popular: true,
  },
  {
    name: "Monthly",
    plan: "monthly" as const,
    price: "2,000",
    duration: "30 days",
    features: ["All predictions", "EV analysis", "Kelly %", "Priority support", "Historical data"],
    icon: Wallet,
  },
];

export default function Subscription() {
  const { user } = useAuth();
  const { pay, isPaying, payError } = usePayment();
  const { subscription } = useSubscription();
  const [selectedPlan, setSelectedPlan] = useState<"daily" | "weekly" | "monthly" | null>(null);
  const [phone, setPhone] = useState("");
  const [paymentSuccess, setPaymentSuccess] = useState(false);

  const handlePay = async (plan: "daily" | "weekly" | "monthly") => {
    if (!user) return;
    setSelectedPlan(plan);
    try {
      await pay(plan, String(user.id), phone || undefined);
      setPaymentSuccess(true);
      setTimeout(() => setPaymentSuccess(false), 5000);
    } catch (e) {
      // Error handled by mutation
    }
  };

  const isActive = subscription?.status === "active";
  const planName = subscription?.plan || "free";

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Subscription</h1>
          <p className="text-sm text-slate-400">Manage your plan and billing</p>
        </div>

        {/* Current Status */}
        <Card className="border-slate-800 bg-slate-900/80 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Current Plan</p>
              <div className="mt-1 flex items-center gap-2">
                <span className="text-xl font-bold text-white capitalize">{planName}</span>
                {isActive && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-success-500/20 px-2 py-0.5 text-xs font-semibold text-success-500 ring-1 ring-success-500/30">
                    <Check className="h-3 w-3" />
                    Active
                  </span>
                )}
                {!isActive && planName !== "free" && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-accent-500/20 px-2 py-0.5 text-xs font-semibold text-accent-500 ring-1 ring-accent-500/30">
                    <Clock className="h-3 w-3" />
                    Expired
                  </span>
                )}
              </div>
              {subscription?.endDate && (
                <p className="mt-1 text-sm text-slate-400">
                  Expires: {new Date(subscription.endDate).toLocaleDateString("en-GB")}
                </p>
              )}
            </div>
            <div className="hidden sm:flex h-12 w-12 items-center justify-center rounded-xl bg-primary-500/10">
              <Sparkles className="h-6 w-6 text-primary-400" />
            </div>
          </div>
        </Card>

        {/* Payment Success */}
        {paymentSuccess && (
          <div className="rounded-lg bg-success-500/10 border border-success-500/20 p-4 flex items-center gap-3">
            <Check className="h-5 w-5 text-success-500" />
            <p className="text-sm text-success-500 font-medium">
              Payment request sent! Check your M-Pesa phone to complete the transaction.
            </p>
          </div>
        )}

        {/* Pay Error */}
        {payError && (
          <div className="rounded-lg bg-danger-500/10 border border-danger-500/20 p-4 flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-danger-500" />
            <p className="text-sm text-danger-500">{payError.message}</p>
          </div>
        )}

        {/* Phone Input */}
        <Card className="border-slate-800 bg-slate-900/80 p-4">
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wider block mb-2">
            M-Pesa Phone Number (optional)
          </label>
          <Input
            placeholder="254712345678"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
          />
          <p className="mt-1 text-xs text-slate-500">Leave blank to use default number</p>
        </Card>

        {/* Plans */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Choose a Plan</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {plans.map((plan) => (
              <Card
                key={plan.name}
                className={cn(
                  "relative border-slate-800 bg-slate-900/80 p-5",
                  plan.popular && "ring-1 ring-accent-500/30 shadow-glow-gold"
                )}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="inline-flex items-center gap-1 rounded-full gradient-gold px-3 py-1 text-xs font-semibold text-slate-900">
                      <Sparkles className="h-3 w-3" />
                      Popular
                    </span>
                  </div>
                )}

                <div className="flex items-center gap-3 mb-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-500/10">
                    <plan.icon className="h-5 w-5 text-primary-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
                    <p className="text-xs text-slate-500">{plan.duration}</p>
                  </div>
                </div>

                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">KES {plan.price}</span>
                </div>

                <ul className="mb-6 space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                      <Check className="h-4 w-4 text-success-500" />
                      {f}
                    </li>
                  ))}
                </ul>

                <MPesaButton
                  onClick={() => handlePay(plan.plan)}
                  loading={isPaying && selectedPlan === plan.plan}
                  disabled={isPaying}
                  className="w-full"
                  variant={plan.popular ? "gold" : "default"}
                >
                  Subscribe
                </MPesaButton>
              </Card>
            ))}
          </div>
        </div>

        {/* Info */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-accent-500 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-slate-300">Important Notice</p>
              <p className="text-xs text-slate-500 mt-1">
                This is a prediction tool, not financial advice. Always gamble responsibly. 
                Past performance does not guarantee future results. Only bet what you can afford to lose.
              </p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
