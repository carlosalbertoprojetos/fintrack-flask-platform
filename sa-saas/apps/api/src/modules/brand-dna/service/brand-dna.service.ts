import { prisma } from "../../../core/prisma/client.js";
import type { UpsertBrandDnaInput } from "../domain/types.js";

export class BrandDnaService {
  async upsert(workspaceId: string, input: UpsertBrandDnaInput) {
    return prisma.brandDna.upsert({
      where: { workspaceId },
      create: {
        workspaceId,
        voiceTone: input.voiceTone,
        authorityPillars: input.authorityPillars,
        forbiddenPatterns: input.forbiddenPatterns,
        lexicalPreferences: input.lexicalPreferences
      },
      update: {
        voiceTone: input.voiceTone,
        authorityPillars: input.authorityPillars,
        forbiddenPatterns: input.forbiddenPatterns,
        lexicalPreferences: input.lexicalPreferences
      }
    });
  }

  async get(workspaceId: string) {
    return prisma.brandDna.findUnique({ where: { workspaceId } });
  }
}
