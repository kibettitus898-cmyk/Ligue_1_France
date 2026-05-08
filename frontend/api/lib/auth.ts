import { createRemoteJWKSet, jwtVerify } from "jose";
import { env } from "./env.js";
import { Errors } from "../../contracts/errors.js";

const JWKS_URL = `${env.SUPABASE_URL}/auth/v1/jwks`;

let jwks: ReturnType<typeof createRemoteJWKSet>;

function getJwks() {
  if (!jwks) {
    jwks = createRemoteJWKSet(new URL(JWKS_URL));
  }
  return jwks;
}

export async function authenticateRequest(headers: Headers) {
  const authHeader = headers.get("authorization");
  const token = authHeader?.replace("Bearer ", "");

  if (!token) {
    throw Errors.forbidden("No authorization token.");
  }

  try {
    const { payload } = await jwtVerify(token, getJwks(), {
      issuer: env.SUPABASE_URL,
      audience: "authenticated",
      clockTolerance: 60,
    });

    return {
      id: payload.sub as string,
      email: payload.email as string,
    };
  } catch (err) {
    console.error("[auth] JWT verification failed:", err);
    throw Errors.forbidden("Invalid authentication token.");
  }
}