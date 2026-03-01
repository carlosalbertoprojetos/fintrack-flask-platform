import type { Request, Response } from "express";
import { asyncHandler } from "../../../core/http/async-handler.js";
import { scoreContentSchema } from "../domain/types.js";
import { ScoringService } from "../service/scoring.service.js";

const service = new ScoringService();

export class ScoringController {
  score = asyncHandler(async (req: Request, res: Response) => {
    const payload = scoreContentSchema.parse(req.body);
    const result = service.score(payload);
    res.status(200).json(result);
  });
}
