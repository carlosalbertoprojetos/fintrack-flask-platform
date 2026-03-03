import { createProvider, PromptOrchestrator } from "@sa/ai-core";
import { prisma } from "../../../core/prisma/client.js";
import { env } from "../../../config/env.js";
import { HttpError } from "../../../core/http/error-handler.js";
import type { Platform, ScoringBreakdown } from "@sa/shared";
import type { CreatePromptTemplateInput, GenerateBundleInput, SingleGenerationInput } from "../domain/types.js";
import { AdaptationService } from "../../adaptation/service/adaptation.service.js";
import { ImagePromptsService } from "../../image-prompts/service/image-prompts.service.js";
import { ScoringService } from "../../scoring/service/scoring.service.js";

const provider = createProvider({
  provider: env.AI_PROVIDER,
  openAiApiKey: env.OPENAI_API_KEY,
  anthropicApiKey: env.ANTHROPIC_API_KEY
});

const orchestrator = new PromptOrchestrator(provider);

export class AiPromptOrchestratorService {
  private readonly adaptation = new AdaptationService();
  private readonly scoring = new ScoringService();
  private readonly imagePrompts = new ImagePromptsService();

  async createPromptTemplate(workspaceId: string, input: CreatePromptTemplateInput) {
    const latest = await prisma.promptTemplate.findFirst({
      where: { workspaceId, module: input.module },
      orderBy: { version: "desc" }
    });

    const nextVersion = (latest?.version ?? 0) + 1;

    return prisma.promptTemplate.create({
      data: {
        workspaceId,
        module: input.module,
        version: nextVersion,
        content: input.content,
        isActive: true
      }
    });
  }

  async listPromptTemplates(workspaceId: string, module?: string) {
    return prisma.promptTemplate.findMany({
      where: {
        workspaceId,
        ...(module ? { module } : {})
      },
      orderBy: [{ module: "asc" }, { version: "desc" }]
    });
  }

  async generateSingle(workspaceId: string, input: SingleGenerationInput) {
    const template = await this.latestPrompt(workspaceId, input.module);
    const systemPrompt = template?.content ?? "You are a social authority strategist.";

    const generated = await orchestrator.run({
      module: input.module,
      systemPrompt,
      userPrompt: `Platform: ${input.platform}\nSource: ${input.sourceText}`,
      temperature: 0.55
    });

    return {
      platform: input.platform,
      text: generated
    };
  }

  async generateBundle(workspaceId: string, input: GenerateBundleInput) {
    const brandDna = await prisma.brandDna.findUnique({ where: { workspaceId } });
    if (!brandDna) {
      throw new HttpError(400, "Brand DNA not configured for workspace");
    }

    const template = await this.latestPrompt(workspaceId, "content_generation");
    const systemPrompt = template?.content ?? "Generate high-authority social content.";

    const adapted = this.adaptation.adapt({
      sourceText: input.sourceText,
      platforms: input.platforms
    });

    const results: Array<{
      platform: Platform;
      adaptedText: string;
      imagePrompt?: string;
      shortFormScript?: string;
      score: ScoringBreakdown;
    }> = [];

    for (const item of adapted) {
      const generatedText = await orchestrator.run({
        module: "content_generation",
        systemPrompt,
        userPrompt: [
          `Voice tone: ${brandDna.voiceTone}`,
          `Authority pillars: ${brandDna.authorityPillars.join(", ")}`,
          `Platform: ${item.platform}`,
          `Draft: ${item.adaptedText}`
        ].join("\n"),
        temperature: 0.5
      });

      const score = this.scoring.score({
        text: generatedText,
        targetVoice: brandDna.voiceTone
      });

      const imagePrompt = input.includeImagePrompt
        ? this.imagePrompts.generate({
            topic: generatedText.slice(0, 80),
            style: "editorial",
            audience: "decision-makers"
          }).prompt
        : undefined;

      const shortFormScript = input.includeShortFormScript
        ? `Hook: ${generatedText.slice(0, 90)}\nBody: ${generatedText.slice(90, 240)}\nCTA: comment "authority".`
        : undefined;

      const created = await prisma.generatedContent.create({
        data: {
          workspaceId,
          strategyId: input.strategyId,
          platform: item.platform,
          sourceText: input.sourceText,
          adaptedText: generatedText,
          imagePrompt,
          shortFormScript,
          persuasionScore: score.total,
          voiceConsistency: score.voiceConsistency
        }
      });

      results.push({
        platform: created.platform,
        adaptedText: created.adaptedText,
        imagePrompt: created.imagePrompt ?? undefined,
        shortFormScript: created.shortFormScript ?? undefined,
        score
      });
    }

    return {
      workspaceId,
      generatedAt: new Date().toISOString(),
      items: results
    };
  }

  private async latestPrompt(workspaceId: string, module: string) {
    return prisma.promptTemplate.findFirst({
      where: {
        workspaceId,
        module,
        isActive: true
      },
      orderBy: { version: "desc" }
    });
  }
}
