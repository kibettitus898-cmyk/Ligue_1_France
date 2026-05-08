import { z } from "zod";
import { createRouter, publicQuery } from "./middleware.js";

const FASTAPI_URL = "http://127.0.0.1:8000"; // Changed from localhost

async function fetchFastAPI(path: string, init?: RequestInit) {
  const url = `${FASTAPI_URL}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const res = await fetch(url, {
      ...init,
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`FastAPI error ${res.status}: ${text}`);
    }
    return res.json();
  } catch (err) {
    clearTimeout(timeout);
    throw err;
  }
}

export const predictionsRouter = createRouter({
  upcoming: publicQuery.query(async () => {
    return fetchFastAPI("/api/v1/predict/upcoming");
  }),

  matches: publicQuery
    .input(z.object({ limit: z.number().optional() }).optional())
    .query(async ({ input }: { input: { limit?: number } | undefined }) => {
      const limit = input?.limit ?? 10;
      return fetchFastAPI(`/api/v1/matches?limit=${limit}`);
    }),

  seasons: publicQuery.query(async () => {
    return fetchFastAPI("/api/v1/matches/seasons");
  }),

  health: publicQuery.query(async () => {
    return fetchFastAPI("/health");
  }),
});