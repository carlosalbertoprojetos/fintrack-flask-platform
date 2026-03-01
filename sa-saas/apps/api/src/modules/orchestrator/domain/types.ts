import { z } from "zod";
import { generateContentInputSchema, platformSchema } from "@sa/shared";

export const createPromptTemplateSchema = z.object({
  module: z.string().min(2),
  content: z.string().min(20)
});

export const generateBundleSchema = generateContentInputSchema;

export const singleGenerationSchema = z.object({
  sourceText: z.string().min(30),
  platform: platformSchema,
  module: z.string().default("content_generation")
});

export type CreatePromptTemplateInput = z.infer<typeof createPromptTemplateSchema>;
export type GenerateBundleInput = z.infer<typeof generateBundleSchema>;
export type SingleGenerationInput = z.infer<typeof singleGenerationSchema>;
