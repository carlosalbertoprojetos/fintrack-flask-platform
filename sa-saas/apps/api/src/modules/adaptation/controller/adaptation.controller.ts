import type { Request, Response } from "express";
import { asyncHandler } from "../../../core/http/async-handler.js";
import { adaptContentSchema } from "../domain/types.js";
import { AdaptationService } from "../service/adaptation.service.js";

const service = new AdaptationService();

export class AdaptationController {
  adapt = asyncHandler(async (req: Request, res: Response) => {
    const payload = adaptContentSchema.parse(req.body);
    const result = service.adapt(payload);
    res.status(200).json(result);
  });
}
