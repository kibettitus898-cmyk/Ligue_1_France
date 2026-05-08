import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().url().optional(),
  SUPABASE_URL: z.string().url().optional().default("http://localhost"),
  SUPABASE_ANON_KEY: z.string().min(1).optional().default("dummy"),
  SUPABASE_JWT_SECRET: z.string().min(1).optional().default("dummy-secret-at-least-32-characters-long"),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1).optional().default("dummy"),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
});

const parsed = envSchema.parse(process.env);

export const env = {
  ...parsed,
  get isProduction() {
    return parsed.NODE_ENV === "production";
  },
};