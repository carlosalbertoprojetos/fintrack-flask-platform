"use client";

import { useEffect, useState } from "react";
import { ApiError, apiGet, apiPost } from "../../lib/api-client";

interface StrategyPanelProps {
  token: string;
}

interface Strategy {
  id: string;
  campaignName: string;
  audiencePersona: string;
  objective: string;
  ctaStyle: string;
  createdAt: string;
}

interface CreateStrategyPayload {
  campaignName: string;
  audiencePersona: string;
  objective: string;
  ctaStyle: string;
}

export function StrategyPanel({ token }: StrategyPanelProps) {
  const [campaignName, setCampaignName] = useState("Q2 Thought Leadership Flywheel");
  const [audiencePersona, setAudiencePersona] = useState("SaaS B2B Founders");
  const [objective, setObjective] = useState("Increase authority and inbound qualified conversations");
  const [ctaStyle, setCtaStyle] = useState("Direct and consultative");
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        const data = await apiGet<Strategy[]>("/api/strategy", token);
        if (!active) {
          return;
        }
        setStrategies(data);
      } catch {
        if (!active) {
          return;
        }
        setError("Failed to load strategies");
      }
    };

    void run();
    return () => {
      active = false;
    };
  }, [token]);

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-ink">Content Strategy Engine</h3>
      <p className="mt-2 text-sm text-slate-600">Create campaign strategy cards tied to persona, objective and CTA style.</p>

      <form
        className="mt-4 grid gap-2"
        onSubmit={async (event) => {
          event.preventDefault();
          setIsLoading(true);
          setError(null);

          try {
            const payload: CreateStrategyPayload = {
              campaignName,
              audiencePersona,
              objective,
              ctaStyle
            };
            const created = await apiPost<CreateStrategyPayload, Strategy>("/api/strategy", payload, token);
            setStrategies((current) => [created, ...current]);
          } catch (caughtError) {
            if (caughtError instanceof ApiError) {
              setError(caughtError.message);
            } else {
              setError("Failed to create strategy");
            }
          } finally {
            setIsLoading(false);
          }
        }}
      >
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={campaignName}
          onChange={(event) => setCampaignName(event.target.value)}
          placeholder="Campaign name"
          minLength={2}
          required
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={audiencePersona}
          onChange={(event) => setAudiencePersona(event.target.value)}
          placeholder="Audience persona"
          minLength={3}
          required
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={objective}
          onChange={(event) => setObjective(event.target.value)}
          placeholder="Objective"
          minLength={3}
          required
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={ctaStyle}
          onChange={(event) => setCtaStyle(event.target.value)}
          placeholder="CTA style"
          minLength={2}
          required
        />

        {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

        <button
          type="submit"
          disabled={isLoading}
          className="rounded-lg bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isLoading ? "Saving..." : "Create Strategy"}
        </button>
      </form>

      <div className="mt-4 space-y-2 text-sm text-slate-700">
        {strategies.slice(0, 3).map((strategy) => (
          <div key={strategy.id} className="rounded-lg border border-slate-200 px-3 py-2">
            <p className="font-medium text-ink">{strategy.campaignName}</p>
            <p className="text-slate-600">{strategy.audiencePersona}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
