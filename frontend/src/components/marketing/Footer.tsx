import { Logo } from "@/components/shared/Logo";
import { Link } from "react-router";
import { Github, Twitter, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <Logo className="mb-4" />
            <p className="text-sm text-slate-400 max-w-sm">
              AI-powered Ligue 1 match predictions with expected value analysis. 
              Built for serious sports bettors in East Africa.
            </p>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Product</h4>
            <ul className="space-y-2">
              <li><Link to="/dashboard" className="text-sm text-slate-400 hover:text-white transition-colors">Dashboard</Link></li>
              <li><Link to="/pricing" className="text-sm text-slate-400 hover:text-white transition-colors">Pricing</Link></li>
              <li><Link to="/predictions" className="text-sm text-slate-400 hover:text-white transition-colors">Predictions</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Legal</h4>
            <ul className="space-y-2">
              <li><span className="text-sm text-slate-400">Terms of Service</span></li>
              <li><span className="text-sm text-slate-400">Privacy Policy</span></li>
              <li><span className="text-sm text-slate-400">Responsible Gambling</span></li>
            </ul>
          </div>
        </div>
        
        <div className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-800 pt-8">
          <p className="text-xs text-slate-500">
            © 2025 Ligue 1 Predictor. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <a href="#" className="text-slate-500 hover:text-white transition-colors">
              <Twitter className="h-4 w-4" />
            </a>
            <a href="#" className="text-slate-500 hover:text-white transition-colors">
              <Github className="h-4 w-4" />
            </a>
            <a href="#" className="text-slate-500 hover:text-white transition-colors">
              <Mail className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
