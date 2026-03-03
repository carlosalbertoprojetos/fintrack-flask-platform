"use client";

import { useEffect, useState } from "react";
import { ApiError, apiGet, apiPost } from "../../lib/api-client";

interface FeedbackPanelProps {
  token: string;
}

type Platform = "LINKEDIN" | "INSTAGRAM" | "X" | "YOUTUBE" | "TIKTOK";

interface FeedbackPayload {
  contentId?: string;
  platform: Platform;
  impressions?: number;
  likes?: number;
  comments?: number;
  shares?: number;
  saves?: number;
  clickThroughRate?: number;
}

interface FeedbackEvent extends FeedbackPayload {
  id: string;
  createdAt: string;
}

interface FeedbackListResponse {
  events: FeedbackEvent[];
  scaffold: {
    message: string;
  };
}

function toNumberOrUndefined(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }

  const parsed = Number(value);
  if (Number.isNaN(parsed)) {
    return undefined;
  }
  return parsed;
}

export function FeedbackPanel({ token }: FeedbackPanelProps) {
  const [platform, setPlatform] = useState<Platform>("LINKEDIN");
  const [contentId, setContentId] = useState("");
  const [impressions, setImpressions] = useState("1200");
  const [likes, setLikes] = useState("84");
  const [comments, setComments] = useState("12");
  const [shares, setShares] = useState("6");
  const [saves, setSaves] = useState("4");
  const [clickThroughRate, setClickThroughRate] = useState("1.8");
  const [events, setEvents] = useState<FeedbackEvent[]>([]);
  const [scaffoldMessage, setScaffoldMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadFeedback = async () => {
    const response = await apiGet<FeedbackListResponse>("/api/feedback", token);
    setEvents(response.events);
    setScaffoldMessage(response.scaffold.message);
  };

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        const response = await apiGet<FeedbackListResponse>("/api/feedback", token);
        if (!active) {
          return;
        }
        setEvents(response.events);
        setScaffoldMessage(response.scaffold.message);
      } catch {
        if (!active) {
          return;
        }
        setError("Failed to load feedback");
      }
    };

    void run();
    return () => {
      active = false;
    };
  }, [token]);

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-ink">Engagement Feedback Layer</h3>
      <p className="mt-2 text-sm text-slate-600">Ingest engagement metrics and inspect the event stream for learning loops.</p>

      <form
        className="mt-4 grid gap-2 md:grid-cols-4"
        onSubmit={async (event) => {
          event.preventDefault();
          setIsLoading(true);
          setError(null);

          try {
            const payload: FeedbackPayload = {
              contentId: contentId || undefined,
              platform,
              impressions: toNumberOrUndefined(impressions),
              likes: toNumberOrUndefined(likes),
              comments: toNumberOrUndefined(comments),
              shares: toNumberOrUndefined(shares),
              saves: toNumberOrUndefined(saves),
              clickThroughRate: toNumberOrUndefined(clickThroughRate)
            };
            await apiPost<FeedbackPayload, FeedbackEvent>("/api/feedback", payload, token);
            await loadFeedback();
          } catch (caughtError) {
            if (caughtError instanceof ApiError) {
              setError(caughtError.message);
            } else {
              setError("Failed to ingest feedback event");
            }
          } finally {
            setIsLoading(false);
          }
        }}
      >
        <select
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={platform}
          onChange={(event) => setPlatform(event.target.value as Platform)}
        >
          <option value="LINKEDIN">LINKEDIN</option>
          <option value="INSTAGRAM">INSTAGRAM</option>
          <option value="X">X</option>
          <option value="YOUTUBE">YOUTUBE</option>
          <option value="TIKTOK">TIKTOK</option>
        </select>
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={contentId}
          onChange={(event) => setContentId(event.target.value)}
          placeholder="contentId (optional)"
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={impressions}
          onChange={(event) => setImpressions(event.target.value)}
          placeholder="impressions"
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={likes}
          onChange={(event) => setLikes(event.target.value)}
          placeholder="likes"
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={comments}
          onChange={(event) => setComments(event.target.value)}
          placeholder="comments"
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={shares}
          onChange={(event) => setShares(event.target.value)}
          placeholder="shares"
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={saves}
          onChange={(event) => setSaves(event.target.value)}
          placeholder="saves"
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-500"
          value={clickThroughRate}
          onChange={(event) => setClickThroughRate(event.target.value)}
          placeholder="CTR"
        />

        <div className="md:col-span-4">
          {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
          <button
            className="mt-2 rounded-lg bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:bg-slate-400"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? "Sending..." : "Ingest Feedback Event"}
          </button>
        </div>
      </form>

      <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-3 text-sm text-slate-700">
        {scaffoldMessage || "Feedback learning loop scaffolded."}
      </div>

      <div className="mt-4 space-y-2 text-sm text-slate-700">
        {events.slice(0, 5).map((event) => (
          <div key={event.id} className="rounded-lg border border-slate-200 p-3">
            <p className="font-medium text-ink">
              {event.platform} | {new Date(event.createdAt).toLocaleString()}
            </p>
            <p>Impressions: {event.impressions ?? 0} | Likes: {event.likes ?? 0} | Comments: {event.comments ?? 0}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
