import type { ImagePromptInput } from "../domain/types.js";

export class ImagePromptsService {
  generate(input: ImagePromptInput) {
    return {
      prompt: `High-authority social visual about ${input.topic}; style ${input.style}; target audience ${input.audience}; cinematic lighting; editorial quality; brand-safe composition.`
    };
  }
}
