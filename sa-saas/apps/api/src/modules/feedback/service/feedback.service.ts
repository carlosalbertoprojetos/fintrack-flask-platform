import { prisma } from "../../../core/prisma/client.js";
import type { IngestEngagementInput } from "../domain/types.js";

export class FeedbackService {
  async ingest(workspaceId: string, input: IngestEngagementInput) {
    return prisma.engagementEvent.create({
      data: {
        workspaceId,
        contentId: input.contentId,
        platform: input.platform,
        impressions: input.impressions,
        likes: input.likes,
        comments: input.comments,
        shares: input.shares,
        saves: input.saves,
        clickThroughRate: input.clickThroughRate
      }
    });
  }

  async list(workspaceId: string) {
    return prisma.engagementEvent.findMany({
      where: { workspaceId },
      orderBy: { createdAt: "desc" },
      take: 200
    });
  }
}
