import { prisma } from "../../../core/prisma/client.js";
import type { CreateStrategyInput } from "../domain/types.js";

export class StrategyService {
  async create(workspaceId: string, input: CreateStrategyInput) {
    return prisma.contentStrategy.create({
      data: {
        workspaceId,
        campaignName: input.campaignName,
        audiencePersona: input.audiencePersona,
        objective: input.objective,
        ctaStyle: input.ctaStyle
      }
    });
  }

  async list(workspaceId: string) {
    return prisma.contentStrategy.findMany({
      where: { workspaceId },
      orderBy: { createdAt: "desc" }
    });
  }
}
