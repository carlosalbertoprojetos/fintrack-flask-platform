import type { AdaptContentInput } from "../domain/types.js";

const platformRules: Record<string, { maxLength: number; styleHint: string }> = {
  LINKEDIN: { maxLength: 2200, styleHint: "professional and insight-led" },
  INSTAGRAM: { maxLength: 2200, styleHint: "visual and concise" },
  X: { maxLength: 280, styleHint: "sharp and provocative" },
  YOUTUBE: { maxLength: 5000, styleHint: "educational and narrative" },
  TIKTOK: { maxLength: 300, styleHint: "fast hook and energetic" }
};

export class AdaptationService {
  adapt(input: AdaptContentInput) {
    return input.platforms.map((platform) => {
      const rule = platformRules[platform];
      const prefix = `[${platform}] ${rule.styleHint}: `;
      const reduced = input.sourceText.slice(0, Math.max(0, rule.maxLength - prefix.length));

      return {
        platform,
        adaptedText: `${prefix}${reduced}`
      };
    });
  }
}
