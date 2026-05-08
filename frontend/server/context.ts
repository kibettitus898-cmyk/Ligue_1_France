import { authenticateRequest } from "./lib/auth.js";

export async function createContext({ req }: { req: Request }) {
  try {
    const user = await authenticateRequest(req.headers);
    return { user };
  } catch {
    return { user: null };
  }
}