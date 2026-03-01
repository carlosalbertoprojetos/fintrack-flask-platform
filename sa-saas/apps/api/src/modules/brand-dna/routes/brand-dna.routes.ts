import { Router } from "express";
import { requireAuth } from "../../../core/middleware/auth.js";
import { BrandDnaController } from "../controller/brand-dna.controller.js";

const controller = new BrandDnaController();

export const brandDnaRouter = Router();

brandDnaRouter.get("/", requireAuth, controller.get);
brandDnaRouter.put("/", requireAuth, controller.upsert);
