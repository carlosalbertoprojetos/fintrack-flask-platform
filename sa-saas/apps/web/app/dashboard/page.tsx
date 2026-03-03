"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Topbar } from "../../components/layout/topbar";
import { Sidebar } from "../../components/layout/sidebar";
import { BrandDnaPanel } from "../../components/engines/brand-dna-panel";
import { StrategyPanel } from "../../components/engines/strategy-panel";
import { OrchestratorPanel } from "../../components/engines/orchestrator-panel";
import { ScoringPanel } from "../../components/engines/scoring-panel";
import { FeedbackPanel } from "../../components/engines/feedback-panel";
import { clearSession, loadSession, type SessionData } from "../../lib/session";

export default function DashboardPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const loaded = loadSession();
    if (!loaded) {
      router.replace("/login");
      return;
    }

    setSession(loaded);
    setIsReady(true);
  }, [router]);

  if (!isReady || !session) {
    return (
      <main className="min-h-screen p-6">
        <div className="mx-auto max-w-7xl rounded-2xl bg-white p-6 text-sm text-slate-600 shadow-sm">Loading workspace...</div>
      </main>
    );
  }

  const handleLogout = () => {
    clearSession();
    router.replace("/login");
  };

  return (
    <main className="min-h-screen p-4 md:p-6">
      <div className="mx-auto grid max-w-7xl gap-4 md:grid-cols-[260px_1fr]">
        <Sidebar />
        <section className="space-y-4">
          <Topbar userName={session.user.fullName} workspaceName={session.workspace.name} onLogout={handleLogout} />
          <div className="grid gap-4 md:grid-cols-2">
            <BrandDnaPanel token={session.token} />
            <StrategyPanel token={session.token} />
            <OrchestratorPanel token={session.token} workspaceId={session.workspace.id} />
            <ScoringPanel token={session.token} />
          </div>
          <FeedbackPanel token={session.token} />
        </section>
      </div>
    </main>
  );
}
