import { z } from "zod";

export const upsertBrandDnaSchema = z.object({
  voiceTone: z.string().min(3),
  authorityPillars: z.array(z.string().min(2)).min(1),
  forbiddenPatterns: z.array(z.string()).default([]),
  lexicalPreferences: z.array(z.string()).default([])
});

export type UpsertBrandDnaInput = z.infer<typeof upsertBrandDnaSchema>;
