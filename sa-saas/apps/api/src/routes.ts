import { Router } from "express";
import { userWorkspaceRouter } from "./modules/user-workspace/routes/user-workspace.routes.js";
import { brandDnaRouter } from "./modules/brand-dna/routes/brand-dna.routes.js";
import { strategyRouter } from "./modules/strategy/routes/strategy.routes.js";
import { adaptationRouter } from "./modules/adaptation/routes/adaptation.routes.js";
import { orchestratorRouter } from "./modules/orchestrator/routes/orchestrator.routes.js";
import { imagePromptsRouter } from "./modules/image-prompts/routes/image-prompts.routes.js";
import { scoringRouter } from "./modules/scoring/routes/scoring.routes.js";
import { feedbackRouter } from "./modules/feedback/routes/feedback.routes.js";

export const apiRouter = Router();

apiRouter.use("/auth", userWorkspaceRouter);
apiRouter.use("/brand-dna", brandDnaRouter);
apiRouter.use("/strategy", strategyRouter);
apiRouter.use("/adaptation", adaptationRouter);
apiRouter.use("/orchestrator", orchestratorRouter);
apiRouter.use("/image-prompts", imagePromptsRouter);
apiRouter.use("/scoring", scoringRouter);
apiRouter.use("/feedback", feedbackRouter);
