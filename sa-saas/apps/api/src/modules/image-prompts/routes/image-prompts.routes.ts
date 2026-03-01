import { Router } from "express";
import { requireAuth } from "../../../core/middleware/auth.js";
import { ImagePromptsController } from "../controller/image-prompts.controller.js";

const controller = new ImagePromptsController();

export const imagePromptsRouter = Router();

imagePromptsRouter.post("/", requireAuth, controller.generate);
