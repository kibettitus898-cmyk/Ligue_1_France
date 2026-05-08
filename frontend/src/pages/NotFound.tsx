import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router";
import { Home, AlertTriangle } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 relative">
      <div className="absolute inset-0 gradient-hero opacity-30" />

      <div className="relative z-10 w-full max-w-sm px-4">
        <Card className="border-slate-800 bg-slate-900/90 text-center">
          <CardHeader className="space-y-4">
            <div className="flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-danger-500/10">
                <AlertTriangle className="h-8 w-8 text-danger-500" />
              </div>
            </div>
            <CardTitle className="text-4xl font-bold text-white">404</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-slate-400">Page not found</p>
            <Button asChild className="w-full gap-2 bg-primary-600 hover:bg-primary-500 text-white">
              <Link to="/">
                <Home className="h-4 w-4" />
                Back to Home
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
