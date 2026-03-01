import type { LlmGenerateParams, LlmProvider } from "./provider.types.js";

export class OpenAIProvider implements LlmProvider {
  public readonly name = "openai" as const;
  private readonly apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async generate(params: LlmGenerateParams): Promise<string> {
    if (!this.apiKey) {
      throw new Error("OPENAI_API_KEY is missing");
    }

    return `OpenAI adapter scaffold output: ${params.userPrompt.slice(0, 180)}`;
  }
}
