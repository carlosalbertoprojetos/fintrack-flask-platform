import { Router } from "express";
import { UserWorkspaceController } from "../controller/user-workspace.controller.js";
import { requireAuth } from "../../../core/middleware/auth.js";

const controller = new UserWorkspaceController();

export const userWorkspaceRouter = Router();

userWorkspaceRouter.post("/register", controller.register);
userWorkspaceRouter.post("/login", controller.login);
userWorkspaceRouter.get("/me", requireAuth, controller.me);
