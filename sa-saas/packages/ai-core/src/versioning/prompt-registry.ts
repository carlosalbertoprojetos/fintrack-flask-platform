export interface PromptVersion {
  module: string;
  version: number;
  content: string;
}

export class PromptRegistry {
  private readonly prompts = new Map<string, PromptVersion>();

  register(prompt: PromptVersion): void {
    this.prompts.set(this.key(prompt.module, prompt.version), prompt);
  }

  get(module: string, version: number): PromptVersion | undefined {
    return this.prompts.get(this.key(module, version));
  }

  latest(module: string): PromptVersion | undefined {
    const options = [...this.prompts.values()].filter((item) => item.module === module);
    if (!options.length) {
      return undefined;
    }
    return options.sort((a, b) => b.version - a.version)[0];
  }

  private key(module: string, version: number): string {
    return `${module}::${version}`;
  }
}
