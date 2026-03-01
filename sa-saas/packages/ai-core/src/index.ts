import { AnthropicProvider } from "./providers/anthropic-provider.js";
import { MockProvider } from "./providers/mock-provider.js";
import { OpenAIProvider } from "./providers/openai-provider.js";
import type { LlmProvider } from "./providers/provider.types.js";

export interface ProviderFactoryParams {
  provider: "mock" | "openai" | "anthropic";
  openAiApiKey?: string;
  anthropicApiKey?: string;
}

export function createProvider(params: ProviderFactoryParams): LlmProvider {
  if (params.provider === "openai") {
    return new OpenAIProvider(params.openAiApiKey ?? "");
  }

  if (params.provider === "anthropic") {
    return new AnthropicProvider(params.anthropicApiKey ?? "");
  }

  return new MockProvider();
}

export * from "./providers/provider.types.js";
export * from "./orchestrator/prompt-orchestrator.js";
export * from "./versioning/prompt-registry.js";
