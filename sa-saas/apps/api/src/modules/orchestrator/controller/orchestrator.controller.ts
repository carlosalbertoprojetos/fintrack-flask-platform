import type { Request, Response } from "express";
import { asyncHandler } from "../../../core/http/async-handler.js";
import {
  createPromptTemplateSchema,
  generateBundleSchema,
  singleGenerationSchema
} from "../domain/types.js";
import { AiPromptOrchestratorService } from "../service/orchestrator.service.js";

const service = new AiPromptOrchestratorService();

export class OrchestratorController {
  createPromptTemplate = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const payload = createPromptTemplateSchema.parse(req.body);
    const result = await service.createPromptTemplate(auth.workspaceId, payload);
    res.status(201).json(result);
  });

  listPromptTemplates = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const moduleName = typeof req.query.module === "string" ? req.query.module : undefined;
    const result = await service.listPromptTemplates(auth.workspaceId, moduleName);
    res.status(200).json(result);
  });

  generateSingle = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const payload = singleGenerationSchema.parse(req.body);
    const result = await service.generateSingle(auth.workspaceId, payload);
    res.status(200).json(result);
  });

  generateBundle = asyncHandler(async (req: Request, res: Response) => {
    const auth = req.auth;
    if (!auth) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const payload = generateBundleSchema.parse(req.body);
    const result = await service.generateBundle(auth.workspaceId, payload);
    res.status(200).json(result);
  });
}
