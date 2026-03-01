import type { LlmProvider } from "../providers/provider.types.js";

export interface OrchestratorInput {
  module: string;
  systemPrompt: string;
  userPrompt: string;
  temperature?: number;
}

export class PromptOrchestrator {
  constructor(private readonly provider: LlmProvider) {}

  async run(input: OrchestratorInput): Promise<string> {
    return this.provider.generate({
      systemPrompt: input.systemPrompt,
      userPrompt: input.userPrompt,
      temperature: input.temperature ?? 0.4,
      maxTokens: 900
    });
  }
}
