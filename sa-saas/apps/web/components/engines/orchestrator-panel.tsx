"use client";

import { useEffect, useState } from "react";
import { ApiError, apiGet, apiPost } from "../../lib/api-client";

interface OrchestratorPanelProps {
  token: string;
  workspaceId: string;
}

type Platform = "LINKEDIN" | "INSTAGRAM" | "X" | "YOUTUBE" | "TIKTOK";

interface PromptTemplate {
  id: string;
  module: string;
  version: number;
  content: string;
  isActive: boolean;
}

interface CreatePromptPayload {
  module: string;
  content: string;
}

interface BundlePayload {
  workspaceId: string;
  strategyId?: string;
  sourceText: string;
  platforms: Platform[];
  includeImagePrompt: boolean;
  includeShortFormScript: boolean;
}

interface BundleResult {
  workspaceId: string;
  generatedAt: string;
  items: Array<{
    platform: Platform;
    adaptedText: string;
    imagePrompt?: string;
    shortFormScript?: string;
    score: {
      total: number;
    };
  }>;
}

const availablePlatforms: Platform[] = ["LINKEDIN", "INSTAGRAM", "X", "YOUTUBE", "TIKTOK"];

export function OrchestratorPanel({ token, workspaceId }: OrchestratorPanelProps) {
  const [moduleName, setModuleName] = useState("content_generation");
  const [templateContent, setTemplateContent] = useState("You are a social authority strategist focused on clarity and persuasion.");
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [sourceText, setSourceText] = useState(
    "Founders confuse posting frequency with authority architecture. Authority grows when repeated insights compound into category-defining frameworks."
  );
  const [platforms, setPlatforms] = useState<Platform[]>(["LINKEDIN", "INSTAGRAM", "X"]);
  const [strategyId, setStrategyId] = useState("");
  const [includeImagePrompt, setIncludeImagePrompt] = useState(true);
  const [includeShortFormScript, setIncludeShortFormScript] = useState(true);
  const [result, setResult] = useState<BundleResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        const data = await apiGet<PromptTemplate[]>("/api/orchestrator/prompts", token);
        if (!active) {
          return;
        }
        setTemplates(data);
      } catch {
        // silent until first template creation
      }
    };

    void run();
    return () => {
      active = false;
    };
  }, [token]);

  const togglePlatform = (platform: Platform) => {
    setPlatforms((current) => {
      if (current.includes(platform)) {
        return current.filter((item) => item !== platform);
      }
      return [...current, platform];
    });
  };

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-ink">AI Prompt Orchestrator</h3>
      <p className="mt-2 text-sm text-slate-600">Version prompts and generate multi-platform bundles from one source text.</p>

      <form
        className="mt-4 space-y-2"
        onSubmit={async (event) => {
          event.preventDefault();
          setError(null);

          try {
            const payload: CreatePromptPayload = {
              module: moduleName,
              content: templateContent
            };
            const created = await apiPost<CreatePromptPayload, PromptTemplate>("/api/orchestrator/prompts", payload, token);
            setTemplates((current) => [created, ...current]);
          } catch (caughtError) {
            if (caughtError instanceof ApiError) {
              setError(caughtError.message);
            } else {
              setError("Failed to create prompt template");
            }
          }
        }}
      >
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={moduleName}
          onChange={(event) => setModuleName(event.target.value)}
          minLength={2}
          required
        />
        <textarea
          className="h-20 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={templateContent}
          onChange={(event) => setTemplateContent(event.target.value)}
          minLength={20}
          required
        />
        <button className="rounded-lg bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-900" type="submit">
          Save Prompt Template
        </button>
      </form>

      <div className="mt-3 space-y-1 text-xs text-slate-600">
        {templates.slice(0, 2).map((template) => (
          <p key={template.id}>
            {template.module} v{template.version}
          </p>
        ))}
      </div>

      <form
        className="mt-4 space-y-3 border-t border-slate-100 pt-4"
        onSubmit={async (event) => {
          event.preventDefault();
          if (platforms.length === 0) {
            setError("Select at least one platform");
            return;
          }

          setIsSubmitting(true);
          setError(null);

          try {
            const payload: BundlePayload = {
              workspaceId,
              strategyId: strategyId || undefined,
              sourceText,
              platforms,
              includeImagePrompt,
              includeShortFormScript
            };
            const generated = await apiPost<BundlePayload, BundleResult>("/api/orchestrator/generate/bundle", payload, token);
            setResult(generated);
          } catch (caughtError) {
            if (caughtError instanceof ApiError) {
              setError(caughtError.message);
            } else {
              setError("Failed to generate bundle");
            }
          } finally {
            setIsSubmitting(false);
          }
        }}
      >
        <textarea
          className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={sourceText}
          onChange={(event) => setSourceText(event.target.value)}
          minLength={30}
          required
        />

        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={strategyId}
          onChange={(event) => setStrategyId(event.target.value)}
          placeholder="Strategy ID (optional)"
        />

        <div className="flex flex-wrap gap-2 text-xs">
          {availablePlatforms.map((platform) => (
            <label key={platform} className="flex items-center gap-1 rounded-lg border border-slate-200 px-2 py-1">
              <input
                type="checkbox"
                checked={platforms.includes(platform)}
                onChange={() => togglePlatform(platform)}
              />
              {platform}
            </label>
          ))}
        </div>

        <div className="flex flex-wrap gap-3 text-sm text-slate-700">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeImagePrompt}
              onChange={(event) => setIncludeImagePrompt(event.target.checked)}
            />
            Image prompt
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeShortFormScript}
              onChange={(event) => setIncludeShortFormScript(event.target.checked)}
            />
            Short-form script
          </label>
        </div>

        {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

        <button
          className="rounded-lg bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:bg-slate-400"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Generating..." : "Generate Bundle"}
        </button>
      </form>

      {result ? (
        <div className="mt-4 space-y-2 text-sm">
          {result.items.map((item) => (
            <div key={`${item.platform}-${item.adaptedText.slice(0, 12)}`} className="rounded-lg border border-slate-200 p-3">
              <p className="font-medium text-ink">
                {item.platform} | score {item.score.total}
              </p>
              <p className="mt-1 line-clamp-3 text-slate-700">{item.adaptedText}</p>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
