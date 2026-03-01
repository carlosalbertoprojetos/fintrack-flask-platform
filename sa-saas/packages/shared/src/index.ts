import { z } from "zod";

export const platformSchema = z.enum(["LINKEDIN", "INSTAGRAM", "X", "YOUTUBE", "TIKTOK"]);
export type Platform = z.infer<typeof platformSchema>;

export const generateContentInputSchema = z.object({
  workspaceId: z.string().min(1),
  strategyId: z.string().optional(),
  sourceText: z.string().min(30),
  platforms: z.array(platformSchema).min(1),
  includeImagePrompt: z.boolean().default(true),
  includeShortFormScript: z.boolean().default(true)
});

export type GenerateContentInput = z.infer<typeof generateContentInputSchema>;

export interface AdaptedContent {
  platform: Platform;
  adaptedText: string;
  imagePrompt?: string;
  shortFormScript?: string;
}

export interface ScoringBreakdown {
  persuasion: number;
  clarity: number;
  authority: number;
  ctaStrength: number;
  voiceConsistency: number;
  total: number;
}
