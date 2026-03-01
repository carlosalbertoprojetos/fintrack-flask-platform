import { z } from "zod";
import { platformSchema } from "@sa/shared";

export const adaptContentSchema = z.object({
  sourceText: z.string().min(30),
  platforms: z.array(platformSchema).min(1)
});

export type AdaptContentInput = z.infer<typeof adaptContentSchema>;
