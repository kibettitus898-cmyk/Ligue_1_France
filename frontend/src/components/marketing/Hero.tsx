import { ArrowRight, TrendingUp, Shield, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 gradient-hero" />
      
      {/* Decorative elements */}
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-5" />
      <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-primary-600/20 blur-3xl" />
      <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-accent-500/10 blur-3xl" />
      
      <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
        <div className="grid gap-12 lg:grid-cols-2 lg:gap-8 items-center">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-primary-600/20 border border-primary-500/30 px-4 py-1.5 text-sm font-medium text-primary-300 mb-6">
              <Zap className="h-4 w-4" />
              AI-Powered Match Predictions
            </div>
            
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Outsmart the Bookies with{" "}
              <span className="text-gradient-gold">Data-Driven Edge</span>
            </h1>
            
            <p className="mt-6 text-lg leading-8 text-slate-300">
              Ligue 1 Predictor uses machine learning to identify value bets with positive expected value (EV). 
              Built for serious bettors in Kenya and East Africa.
            </p>
            
            <div className="mt-8 flex flex-wrap gap-4">
              <Link to="/dashboard">
                <Button size="lg" className="gap-2 bg-primary-600 hover:bg-primary-500 text-white px-8">
                  Get Predictions
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/pricing">
                <Button size="lg" variant="outline" className="border-slate-600 text-slate-200 hover:bg-slate-800 px-8">
                  View Pricing
                </Button>
              </Link>
            </div>
            
            <div className="mt-10 flex items-center gap-6 text-sm text-slate-400">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-success-500" />
                <span>+12.4% ROI</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-primary-500" />
                <span>94% Accuracy</span>
              </div>
            </div>
          </div>
          
          <div className="relative lg:ml-12">
            <div className="relative rounded-2xl border border-slate-700/50 bg-slate-900/80 p-6 shadow-glow">
              <div className="absolute -top-3 -right-3">
                <span className="inline-flex items-center rounded-full bg-success-500/20 px-3 py-1 text-xs font-semibold text-success-500 ring-1 ring-success-500/30">
                  VALUE BET
                </span>
              </div>
              
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-900/50 text-sm font-bold text-primary-300">
                    PSG
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">Paris SG</p>
                    <p className="text-xs text-slate-400">Home</p>
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-xs text-slate-500">vs</p>
                  <p className="text-xs text-accent-400 font-semibold">Today 20:00</p>
                </div>
                <div className="flex items-center gap-3 text-right">
                  <div>
                    <p className="text-sm font-semibold text-white">Marseille</p>
                    <p className="text-xs text-slate-400">Away</p>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-900/50 text-sm font-bold text-primary-300">
                    OM
                  </div>
                </div>
              </div>
              
              <div className="mt-4 grid grid-cols-3 gap-3">
                <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                  <p className="text-lg font-bold text-white">62%</p>
                  <p className="text-xs text-slate-400">Home Win</p>
                </div>
                <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                  <p className="text-lg font-bold text-white">22%</p>
                  <p className="text-xs text-slate-400">Draw</p>
                </div>
                <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                  <p className="text-lg font-bold text-white">16%</p>
                  <p className="text-xs text-slate-400">Away Win</p>
                </div>
              </div>
              
              <div className="mt-4 flex items-center justify-between rounded-lg bg-success-500/10 p-3 ring-1 ring-success-500/20">
                <div>
                  <p className="text-xs text-slate-400">Recommended Bet</p>
                  <p className="text-sm font-semibold text-success-500">PSG Win @ 1.65</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-400">EV</p>
                  <p className="text-sm font-bold text-success-500">+8.4%</p>
                </div>
              </div>
              
              <div className="mt-3 flex items-center gap-2">
                <div className="h-2 flex-1 rounded-full bg-slate-800">
                  <div className="h-2 rounded-full bg-primary-500" style={{ width: "78%" }} />
                </div>
                <span className="text-xs font-medium text-primary-400">78% Confidence</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
