import type { ScoringBreakdown } from "@sa/shared";
import type { ScoreContentInput } from "../domain/types.js";

export class ScoringService {
  score(input: ScoreContentInput): ScoringBreakdown {
    const length = input.text.length;
    const ctaStrength = /(agende|comente|responda|acesse|fale comigo)/i.test(input.text) ? 90 : 55;
    const authority = /(framework|metodologia|benchmark|dados|case)/i.test(input.text) ? 88 : 62;
    const clarity = length > 80 && length < 800 ? 82 : 65;
    const persuasion = Math.min(95, Math.max(52, Math.round((ctaStrength + authority + clarity) / 3)));
    const voiceConsistency = input.text.toLowerCase().includes(input.targetVoice.toLowerCase()) ? 85 : 68;

    const total = Math.round((persuasion + clarity + authority + ctaStrength + voiceConsistency) / 5);

    return {
      persuasion,
      clarity,
      authority,
      ctaStrength,
      voiceConsistency,
      total
    };
  }
}
