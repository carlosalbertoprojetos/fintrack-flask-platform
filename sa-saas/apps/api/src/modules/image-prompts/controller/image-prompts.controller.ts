import type { Request, Response } from "express";
import { asyncHandler } from "../../../core/http/async-handler.js";
import { imagePromptSchema } from "../domain/types.js";
import { ImagePromptsService } from "../service/image-prompts.service.js";

const service = new ImagePromptsService();

export class ImagePromptsController {
  generate = asyncHandler(async (req: Request, res: Response) => {
    const payload = imagePromptSchema.parse(req.body);
    const result = service.generate(payload);
    res.status(200).json(result);
  });
}
