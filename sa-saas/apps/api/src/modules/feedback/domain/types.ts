import { z } from "zod";
import { platformSchema } from "@sa/shared";

export const ingestEngagementSchema = z.object({
  contentId: z.string().optional(),
  platform: platformSchema,
  impressions: z.number().int().nonnegative().optional(),
  likes: z.number().int().nonnegative().optional(),
  comments: z.number().int().nonnegative().optional(),
  shares: z.number().int().nonnegative().optional(),
  saves: z.number().int().nonnegative().optional(),
  clickThroughRate: z.number().nonnegative().optional()
});

export type IngestEngagementInput = z.infer<typeof ingestEngagementSchema>;
