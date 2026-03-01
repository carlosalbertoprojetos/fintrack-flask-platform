import type { LlmGenerateParams, LlmProvider } from "./provider.types.js";

export class AnthropicProvider implements LlmProvider {
  public readonly name = "anthropic" as const;
  private readonly apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async generate(params: LlmGenerateParams): Promise<string> {
    if (!this.apiKey) {
      throw new Error("ANTHROPIC_API_KEY is missing");
    }

    return `Anthropic adapter scaffold output: ${params.userPrompt.slice(0, 180)}`;
  }
}
