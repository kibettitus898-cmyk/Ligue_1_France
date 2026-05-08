import type { ReactNode } from "react";

export function AuthGuard({ children }: { children: ReactNode }) {
  // TEMPORARILY BYPASSED — all content loads without login
  return <>{children}</>;
}