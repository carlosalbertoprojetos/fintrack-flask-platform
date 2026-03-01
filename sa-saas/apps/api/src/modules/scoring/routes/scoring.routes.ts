import { Router } from "express";
import { requireAuth } from "../../../core/middleware/auth.js";
import { ScoringController } from "../controller/scoring.controller.js";

const controller = new ScoringController();

export const scoringRouter = Router();

scoringRouter.post("/", requireAuth, controller.score);
