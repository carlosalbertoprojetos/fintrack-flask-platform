import type { Request, Response } from "express";
import { asyncHandler } from "../../../core/http/async-handler.js";
import { createStrategySchema } from "../domain/types.js";
import { StrategyService } from "../service/strategy.service.js";

const service = new StrategyService();

export class StrategyController {
  create = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const payload = createStrategySchema.parse(req.body);
    const result = await service.create(auth.workspaceId, payload);
    res.status(201).json(result);
  });

  list = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const result = await service.list(auth.workspaceId);
    res.status(200).json(result);
  });
}
