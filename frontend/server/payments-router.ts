import { z } from "zod";
import { createRouter, publicQuery } from "./middleware.js";

const FASTAPI_URL = "http://127.0.0.1:8000";

async function fetchFastAPI(path: string, init?: RequestInit) {
  const res = await fetch(`${FASTAPI_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`FastAPI error ${res.status}: ${text}`);
  }
  return res.json();
}

export const paymentsRouter = createRouter({
  getSubscription: publicQuery
    .input(z.object({ userId: z.string() }))
    .query(async ({ input }: { input: { userId: string } }) => {
      return fetchFastAPI(`/api/v1/payments/subscription/${input.userId}`);
    }),

  cancelSubscription: publicQuery
    .input(z.object({ userId: z.string() }))
    .mutation(async ({ input }: { input: { userId: string } }) => {
      return fetchFastAPI(`/api/v1/payments/subscription/${input.userId}`, {
        method: "DELETE",
      });
    }),

  mockStkPush: publicQuery
    .input(z.object({ phone: z.string(), amount: z.number() }).optional())
    .mutation(async ({ input }: { input: { phone: string; amount: number } | undefined }) => {
      return fetchFastAPI("/api/v1/payments/mock-stk-push", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input ?? {}),
      });
    }),
});