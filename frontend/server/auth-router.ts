import { createRouter, publicQuery } from "./middleware.js";

export const authRouter = createRouter({
  me: publicQuery.query(async ({ ctx }: { ctx: any }) => {
    return ctx.user ?? null;
  }),
});