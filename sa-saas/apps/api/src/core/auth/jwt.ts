import jwt from "jsonwebtoken";
import { env } from "../../config/env.js";

export interface AuthTokenPayload {
  userId: string;
  workspaceId: string;
}

export function signToken(payload: AuthTokenPayload): string {
  return jwt.sign(payload, env.JWT_SECRET, { expiresIn: "12h" });
}

export function verifyToken(token: string): AuthTokenPayload {
  const decoded = jwt.verify(token, env.JWT_SECRET);
  if (typeof decoded === "string") {
    throw new Error("Invalid token payload");
  }
  return decoded as AuthTokenPayload;
}
