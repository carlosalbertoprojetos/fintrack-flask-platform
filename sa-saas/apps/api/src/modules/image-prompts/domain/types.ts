import { z } from "zod";

export const imagePromptSchema = z.object({
  topic: z.string().min(3),
  style: z.string().min(2),
  audience: z.string().min(2)
});

export type ImagePromptInput = z.infer<typeof imagePromptSchema>;
