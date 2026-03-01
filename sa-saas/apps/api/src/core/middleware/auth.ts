import type { NextFunction, Request, Response } from "express";
import { HttpError } from "../http/error-handler.js";
import { verifyToken } from "../auth/jwt.js";

declare global {
  namespace Express {
    interface Request {
      auth?: {
        userId: string;
        workspaceId: string;
      };
    }
  }
}

export function requireAuth(req: Request, _res: Response, next: NextFunction): void {
  const authorization = req.headers.authorization;
  if (!authorization?.startsWith("Bearer ")) {
    throw new HttpError(401, "Missing bearer token");
  }

  const token = authorization.slice("Bearer ".length);
  const payload = verifyToken(token);
  req.auth = payload;
  next();
}
