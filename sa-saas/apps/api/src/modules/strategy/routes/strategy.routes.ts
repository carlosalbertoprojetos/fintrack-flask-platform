import { Router } from "express";
import { requireAuth } from "../../../core/middleware/auth.js";
import { StrategyController } from "../controller/strategy.controller.js";

const controller = new StrategyController();

export const strategyRouter = Router();

strategyRouter.get("/", requireAuth, controller.list);
strategyRouter.post("/", requireAuth, controller.create);
