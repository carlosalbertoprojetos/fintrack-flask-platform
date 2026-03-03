"use client";

import { useEffect, useState } from "react";
import { ApiError, apiGet, apiPut } from "../../lib/api-client";

interface BrandDnaPanelProps {
  token: string;
}

interface BrandDnaPayload {
  voiceTone: string;
  authorityPillars: string[];
  forbiddenPatterns: string[];
  lexicalPreferences: string[];
}

interface BrandDnaResponse extends BrandDnaPayload {
  id: string;
  workspaceId: string;
}

function csvToArray(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export function BrandDnaPanel({ token }: BrandDnaPanelProps) {
  const [voiceTone, setVoiceTone] = useState("strategic, direct, executive");
  const [authorityPillars, setAuthorityPillars] = useState("growth architecture, GTM clarity, authority assets");
  const [forbiddenPatterns, setForbiddenPatterns] = useState("");
  const [lexicalPreferences, setLexicalPreferences] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        const data = await apiGet<BrandDnaResponse | null>("/api/brand-dna", token);
        if (!active || !data) {
          return;
        }

        setVoiceTone(data.voiceTone);
        setAuthorityPillars(data.authorityPillars.join(", "));
        setForbiddenPatterns(data.forbiddenPatterns.join(", "));
        setLexicalPreferences(data.lexicalPreferences.join(", "));
      } catch {
        // silent on first load when DNA is not configured yet
      }
    };

    void run();
    return () => {
      active = false;
    };
  }, [token]);

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-ink">Brand DNA Engine</h3>
      <p className="mt-2 text-sm text-slate-600">Configure voice and linguistic rules used by generation and scoring pipelines.</p>

      <form
        className="mt-4 space-y-3"
        onSubmit={async (event) => {
          event.preventDefault();
          setIsLoading(true);
          setMessage(null);
          setError(null);

          try {
            const payload: BrandDnaPayload = {
              voiceTone,
              authorityPillars: csvToArray(authorityPillars),
              forbiddenPatterns: csvToArray(forbiddenPatterns),
              lexicalPreferences: csvToArray(lexicalPreferences)
            };

            await apiPut<BrandDnaPayload, BrandDnaResponse>("/api/brand-dna", payload, token);
            setMessage("Brand DNA saved");
          } catch (caughtError) {
            if (caughtError instanceof ApiError) {
              setError(caughtError.message);
            } else {
              setError("Failed to save Brand DNA");
            }
          } finally {
            setIsLoading(false);
          }
        }}
      >
        <label className="block text-sm text-slate-700">
          Voice tone
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
            value={voiceTone}
            onChange={(event) => setVoiceTone(event.target.value)}
            minLength={3}
            required
          />
        </label>

        <label className="block text-sm text-slate-700">
          Authority pillars (comma-separated)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
            value={authorityPillars}
            onChange={(event) => setAuthorityPillars(event.target.value)}
            required
          />
        </label>

        <label className="block text-sm text-slate-700">
          Forbidden patterns (comma-separated)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
            value={forbiddenPatterns}
            onChange={(event) => setForbiddenPatterns(event.target.value)}
          />
        </label>

        <label className="block text-sm text-slate-700">
          Lexical preferences (comma-separated)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
            value={lexicalPreferences}
            onChange={(event) => setLexicalPreferences(event.target.value)}
          />
        </label>

        {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
        {message ? <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}

        <button
          type="submit"
          disabled={isLoading}
          className="rounded-lg bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isLoading ? "Saving..." : "Save Brand DNA"}
        </button>
      </form>
    </section>
  );
}
