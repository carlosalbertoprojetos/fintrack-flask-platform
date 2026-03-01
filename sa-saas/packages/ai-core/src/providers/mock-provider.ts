import type { LlmGenerateParams, LlmProvider } from "./provider.types.js";

export class MockProvider implements LlmProvider {
  public readonly name = "mock" as const;

  async generate(params: LlmGenerateParams): Promise<string> {
    const snippet = params.userPrompt.slice(0, 180);
    return `[MOCK:${this.name}] ${snippet}`;
  }
}
