import type { Request, Response } from "express";
import { asyncHandler } from "../../../core/http/async-handler.js";
import { ingestEngagementSchema } from "../domain/types.js";
import { FeedbackService } from "../service/feedback.service.js";

const service = new FeedbackService();

export class FeedbackController {
  ingest = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const payload = ingestEngagementSchema.parse(req.body);
    const result = await service.ingest(auth.workspaceId, payload);
    res.status(201).json(result);
  });

  list = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const result = await service.list(auth.workspaceId);
    res.status(200).json({
      events: result,
      scaffold: {
        message: "Feedback learning loop scaffolded. Modeling and training jobs can be attached here."
      }
    });
  });
}
