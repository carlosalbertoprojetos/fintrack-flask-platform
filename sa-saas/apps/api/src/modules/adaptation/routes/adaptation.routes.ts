import { Router } from "express";
import { requireAuth } from "../../../core/middleware/auth.js";
import { AdaptationController } from "../controller/adaptation.controller.js";

const controller = new AdaptationController();

export const adaptationRouter = Router();

adaptationRouter.post("/", requireAuth, controller.adapt);
