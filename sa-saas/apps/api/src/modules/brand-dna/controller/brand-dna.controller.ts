import type { Request, Response } from "express";
import { asyncHandler } from "../../../core/http/async-handler.js";
import { upsertBrandDnaSchema } from "../domain/types.js";
import { BrandDnaService } from "../service/brand-dna.service.js";

const service = new BrandDnaService();

export class BrandDnaController {
  upsert = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const payload = upsertBrandDnaSchema.parse(req.body);
    const result = await service.upsert(auth.workspaceId, payload);
    res.status(200).json(result);
  });

  get = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const result = await service.get(auth.workspaceId);
    res.status(200).json(result);
  });
}
