import type { HealthResponse } from "../lib/types";

export type HealthState =
  | { kind: "checking" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "down"; message: string };

export function Header({ health, onRecheck }: { health: HealthState; onRecheck: () => void }) {
  let dot = "bg-muted";
  let text = "Checking API…";
  if (health.kind === "ok") {
    dot = health.data.council_configured ? "bg-pos" : "bg-warn";
    text = health.data.council_configured ? "API online" : "API online · council not configured";
  } else if (health.kind === "down") {
    dot = "bg-neg";
    text = "API unreachable";
  }

  return (
    <header className="border-b border-line bg-bg/95">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-3">
          <svg viewBox="0 0 32 32" className="h-7 w-7 shrink-0" aria-hidden="true">
            <rect width="32" height="32" rx="3" fill="#161b22" stroke="#2f3843" />
            <path d="M6 22 L12 15 L17 19 L26 9" fill="none" stroke="#3987e5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <div>
            <h1 className="text-[15px] font-semibold tracking-wide text-ink">Finance Decision Council</h1>
            <p className="text-xs text-muted">Multi-agent valuation · risk · momentum analysis with explicit disagreement reporting</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onRecheck}
          title={health.kind === "down" ? health.message : "Re-check backend health"}
          className="flex items-center gap-2 border border-line px-2.5 py-1 font-mono text-[11px] uppercase tracking-wider text-ink-2 hover:border-line-strong"
        >
          <span className={`h-1.5 w-1.5 rounded-full ${dot} ${health.kind === "checking" ? "animate-pulse" : ""}`} />
          {text}
          {health.kind === "ok" && health.data.model && <span className="hidden text-muted md:inline">· {health.data.model}</span>}
        </button>
      </div>
    </header>
  );
}
