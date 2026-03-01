import { z } from "zod";

export const scoreContentSchema = z.object({
  text: z.string().min(20),
  targetVoice: z.string().min(3)
});

export type ScoreContentInput = z.infer<typeof scoreContentSchema>;
