import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/shared/Logo";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  LayoutDashboard,
  BarChart3,
  CalendarDays,
  CreditCard,
  Menu,
  X,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { AuthGuard } from "@/components/shared/AuthGuard";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Predictions", href: "/predictions", icon: BarChart3 },
  { name: "Fixtures", href: "/fixtures", icon: CalendarDays },
  { name: "Subscription", href: "/subscription", icon: CreditCard },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, signOut, loading } = useAuth();  // fixed: signOut instead of logout, loading instead of isLoading
  const location = useLocation();

  // Get display name from user metadata or fallback to email
  const displayName = user?.user_metadata?.name || user?.email || "User";
  const displayEmail = user?.email || "";
  const avatarInitial = displayName.charAt(0).toUpperCase();

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-full w-64 border-r border-slate-800 bg-slate-900 transition-transform duration-300 lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center border-b border-slate-800 px-4">
          <Logo />
          <button
            className="ml-auto lg:hidden p-2 text-slate-400"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-col gap-1 p-3">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary-600/10 text-primary-400"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                )}
              >
                <item.icon className={cn("h-4 w-4", isActive ? "text-primary-400" : "text-slate-500")} />
                {item.name}
                {isActive && <ChevronRight className="ml-auto h-4 w-4" />}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-slate-800 p-4">
          <div className="flex items-center gap-3 mb-3">
            <Avatar className="h-8 w-8 border border-slate-700">
              <AvatarFallback className="bg-primary-600 text-white text-xs">
                {avatarInitial}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{displayName}</p>
              <p className="text-xs text-slate-500 truncate">{displayEmail}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-slate-400 hover:text-white hover:bg-slate-800"
            onClick={signOut}  // fixed: signOut instead of logout
            disabled={loading}  // fixed: loading instead of isLoading
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Header */}
        <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
          <div className="flex h-16 items-center gap-4 px-4">
            <button
              className="lg:hidden p-2 text-slate-400"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex-1" />
            <div className="flex items-center gap-3">
              <span className="hidden sm:inline-flex items-center rounded-full bg-success-500/10 px-2.5 py-0.5 text-xs font-medium text-success-500 ring-1 ring-success-500/20">
                API Online
              </span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 sm:p-6 lg:p-8">
          <AuthGuard>{children}</AuthGuard>
        </main>
      </div>
    </div>
  );
}