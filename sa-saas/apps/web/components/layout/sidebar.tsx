export function Sidebar() {
  const items = [
    "Workspace",
    "Brand DNA",
    "Strategy",
    "Adaptation",
    "Prompt Orchestrator",
    "Image Prompts",
    "Scoring",
    "Feedback"
  ];

  return (
    <aside className="w-full rounded-2xl bg-ink p-5 text-white md:w-64">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-300">SA SaaS</p>
      <h2 className="mt-2 text-xl font-semibold">Control Room</h2>
      <ul className="mt-6 space-y-2 text-sm">
        {items.map((item) => (
          <li key={item} className="rounded-lg px-3 py-2 transition hover:bg-white/10">
            {item}
          </li>
        ))}
      </ul>
    </aside>
  );
}
