import { authRouter } from "./auth-router.js";
import { predictionsRouter } from "./predictions-router.js";
import { paymentsRouter } from "./payments-router.js";
import { createRouter, publicQuery } from "./middleware.js";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),
  auth: authRouter,
  predictions: predictionsRouter,
  payments: paymentsRouter,
});

export type AppRouter = typeof appRouter;