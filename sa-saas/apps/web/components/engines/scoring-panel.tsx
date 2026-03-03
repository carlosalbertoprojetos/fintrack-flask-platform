"use client";

import { useState } from "react";
import { ApiError, apiPost } from "../../lib/api-client";

interface ScoringPanelProps {
  token: string;
}

interface ScorePayload {
  text: string;
  targetVoice: string;
}

interface ScoreResponse {
  persuasion: number;
  clarity: number;
  authority: number;
  ctaStrength: number;
  voiceConsistency: number;
  total: number;
}

export function ScoringPanel({ token }: ScoringPanelProps) {
  const [text, setText] = useState(
    "Framework-driven post for founders: start with data, show methodology, and end with a direct CTA to continue the conversation."
  );
  const [targetVoice, setTargetVoice] = useState("strategic");
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-ink">Content Scoring Engine</h3>
      <p className="mt-2 text-sm text-slate-600">Score persuasion, authority, clarity, CTA strength and voice consistency.</p>

      <form
        className="mt-4 space-y-3"
        onSubmit={async (event) => {
          event.preventDefault();
          setIsLoading(true);
          setError(null);

          try {
            const payload: ScorePayload = { text, targetVoice };
            const scored = await apiPost<ScorePayload, ScoreResponse>("/api/scoring", payload, token);
            setResult(scored);
          } catch (caughtError) {
            if (caughtError instanceof ApiError) {
              setError(caughtError.message);
            } else {
              setError("Failed to score content");
            }
          } finally {
            setIsLoading(false);
          }
        }}
      >
        <textarea
          className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={text}
          onChange={(event) => setText(event.target.value)}
          minLength={20}
          required
        />
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={targetVoice}
          onChange={(event) => setTargetVoice(event.target.value)}
          minLength={3}
          required
        />
        {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
        <button
          className="rounded-lg bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:bg-slate-400"
          type="submit"
          disabled={isLoading}
        >
          {isLoading ? "Scoring..." : "Score Content"}
        </button>
      </form>

      {result ? (
        <div className="mt-4 grid grid-cols-2 gap-2 text-sm md:grid-cols-3">
          {[
            ["Persuasion", result.persuasion],
            ["Authority", result.authority],
            ["Clarity", result.clarity],
            ["CTA", result.ctaStrength],
            ["Voice", result.voiceConsistency],
            ["Total", result.total]
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-slate-200 p-3 text-center">
              <p className="text-xs text-slate-500">{label}</p>
              <p className="mt-1 text-lg font-semibold text-ink">{String(value)}</p>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
