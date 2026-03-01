export interface LlmGenerateParams {
  systemPrompt: string;
  userPrompt: string;
  temperature?: number;
  maxTokens?: number;
}

export interface LlmProvider {
  name: "mock" | "openai" | "anthropic";
  generate(params: LlmGenerateParams): Promise<string>;
}
