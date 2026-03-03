import { Router } from "express";
import { requireAuth } from "../../../core/middleware/auth.js";
import { FeedbackController } from "../controller/feedback.controller.js";

const controller = new FeedbackController();

export const feedbackRouter = Router();

feedbackRouter.get("/", requireAuth, controller.list);
feedbackRouter.post("/", requireAuth, controller.ingest);
