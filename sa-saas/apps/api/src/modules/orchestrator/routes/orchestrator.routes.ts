import { Router } from "express";
import { requireAuth } from "../../../core/middleware/auth.js";
import { OrchestratorController } from "../controller/orchestrator.controller.js";

const controller = new OrchestratorController();

export const orchestratorRouter = Router();

orchestratorRouter.get("/prompts", requireAuth, controller.listPromptTemplates);
orchestratorRouter.post("/prompts", requireAuth, controller.createPromptTemplate);
orchestratorRouter.post("/generate/single", requireAuth, controller.generateSingle);
orchestratorRouter.post("/generate/bundle", requireAuth, controller.generateBundle);
