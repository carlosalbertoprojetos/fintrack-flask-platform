"use client";

interface TopbarProps {
  userName: string;
  workspaceName: string;
  onLogout: () => void;
}

export function Topbar({ userName, workspaceName, onLogout }: TopbarProps) {
  return (
    <header className="rounded-2xl bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Social Authority</p>
          <h1 className="mt-1 text-2xl font-semibold text-ink">SaaS Intelligence Dashboard</h1>
        </div>
        <div className="flex items-center gap-2">
          <div className="rounded-xl bg-slate-100 px-3 py-2 text-sm text-slate-700">
            {workspaceName} | {userName}
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="rounded-xl bg-ink px-3 py-2 text-sm text-white transition hover:bg-slate-900"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
