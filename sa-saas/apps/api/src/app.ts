import express from "express";
import cors from "cors";
import { errorHandler } from "./core/http/error-handler.js";
import { logger } from "./core/http/logger.js";
import { apiRouter } from "./routes.js";

export function createApp() {
  const app = express();

  app.use(cors());
  app.use(express.json({ limit: "1mb" }));

  app.get("/health", (_req, res) => {
    res.status(200).json({ status: "ok" });
  });

  app.use("/api", apiRouter);
  app.use(errorHandler);

  logger.info("API app initialized");
  return app;
}
