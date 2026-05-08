import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router";
import { Logo } from "@/components/shared/Logo";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { Menu, X, LayoutDashboard } from "lucide-react";

export function MarketingNav() {
  const { isAuthenticated } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const isHome = location.pathname === "/";

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled || !isHome
          ? "bg-slate-950/90 backdrop-blur-md border-b border-slate-800"
          : "bg-transparent"
      }`}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Logo />
          
          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            <Link to="/" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Home
            </Link>
            <Link to="/pricing" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Pricing
            </Link>
            {isAuthenticated && (
              <Link to="/dashboard" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                Dashboard
              </Link>
            )}
          </nav>
          
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <Link to="/dashboard">
                <Button size="sm" className="gap-2 bg-primary-600 hover:bg-primary-500 text-white">
                  <LayoutDashboard className="h-4 w-4" />
                  Dashboard
                </Button>
              </Link>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-slate-800">
                    Log in
                  </Button>
                </Link>
                <Link to="/pricing">
                  <Button size="sm" className="bg-primary-600 hover:bg-primary-500 text-white">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>
          
          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 text-slate-300"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>
      
      {/* Mobile nav */}
      {mobileOpen && (
        <div className="md:hidden bg-slate-950 border-b border-slate-800 px-4 py-4 space-y-3">
          <Link to="/" className="block text-sm font-medium text-slate-300" onClick={() => setMobileOpen(false)}>
            Home
          </Link>
          <Link to="/pricing" className="block text-sm font-medium text-slate-300" onClick={() => setMobileOpen(false)}>
            Pricing
          </Link>
          {isAuthenticated && (
            <Link to="/dashboard" className="block text-sm font-medium text-slate-300" onClick={() => setMobileOpen(false)}>
              Dashboard
            </Link>
          )}
          {isAuthenticated ? (
            <Link to="/dashboard" onClick={() => setMobileOpen(false)}>
              <Button size="sm" className="w-full bg-primary-600 text-white">
                Dashboard
              </Button>
            </Link>
          ) : (
            <Link to="/login" onClick={() => setMobileOpen(false)}>
              <Button size="sm" variant="outline" className="w-full border-slate-700 text-slate-300">
                Log in
              </Button>
            </Link>
          )}
        </div>
      )}
    </header>
  );
}
