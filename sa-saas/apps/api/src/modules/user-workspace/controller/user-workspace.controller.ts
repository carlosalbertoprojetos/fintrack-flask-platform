import type { Request, Response } from "express";
import { asyncHandler } from "../../../core/http/async-handler.js";
import { loginSchema, registerUserSchema } from "../domain/types.js";
import { UserWorkspaceService } from "../service/user-workspace.service.js";

const service = new UserWorkspaceService();

export class UserWorkspaceController {
  register = asyncHandler(async (req: Request, res: Response) => {
    const payload = registerUserSchema.parse(req.body);
    const result = await service.register(payload);
    res.status(201).json(result);
  });

  login = asyncHandler(async (req: Request, res: Response) => {
    const payload = loginSchema.parse(req.body);
    const result = await service.login(payload);
    res.status(200).json(result);
  });

  me = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const result = await service.me(auth.userId, auth.workspaceId);
    res.status(200).json(result);
  });
}
