/**
 * Generated by orval v6.31.0 🍺
 * Do not edit manually.
 * Workout API
 * A workout tracking API built with FastAPI
 * OpenAPI spec version: 1.0.0
 */
import type { NextAuthUserResponse } from "./nextAuthUserResponse";

/**
 * Auth.js token verification response.
 */
export interface AuthTokenResponse {
  /** Backend session token for API access */
  session_token: string;
  /** User information */
  user: NextAuthUserResponse;
}
