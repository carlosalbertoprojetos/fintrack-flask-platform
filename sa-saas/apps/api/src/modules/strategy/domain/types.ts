import { z } from "zod";

export const createStrategySchema = z.object({
  campaignName: z.string().min(2),
  audiencePersona: z.string().min(3),
  objective: z.string().min(3),
  ctaStyle: z.string().min(2)
});

export type CreateStrategyInput = z.infer<typeof createStrategySchema>;
