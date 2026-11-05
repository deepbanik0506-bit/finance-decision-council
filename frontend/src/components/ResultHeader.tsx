import type { AnalysisResponse } from "../lib/types";
import { compact, dateTime, label, money } from "../lib/format";
import { Badge, Stat } from "./ui";

function exportJson(data: AnalysisResponse) {
  // Exports the API response object exactly as received.
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const href = URL.createObjectURL(blob);
  const stamp = data.analyzed_at.replace(/[:.]/g, "-");
  const a = document.createElement("a");
  a.href = href;
  a.download = `fdc-${data.ticker}-${stamp}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(href);
}

export function ResultHeader({ data }: { data: AnalysisResponse }) {
  const ev = data.market_evidence;
  return (
    <section className="border border-line bg-panel">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line px-4 py-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-mono text-2xl font-semibold tracking-wide text-ink">{data.ticker}</span>
            <Badge value={data.status === "complete" ? "all agents executed" : "partial execution"} tone={data.status === "complete" ? "pos" : "warn"} />
          </div>
          <p className="mt-0.5 truncate text-sm text-ink-2">
            {ev.company_name ?? "Company name unavailable"}
            {ev.sector && <span className="text-muted"> · {ev.sector}</span>}
            {ev.industry && <span className="text-muted"> · {ev.industry}</span>}
          </p>
        </div>
        <button
          type="button"
          onClick={() => exportJson(data)}
          className="border border-line-strong bg-panel-2 px-3 py-1.5 font-mono text-xs uppercase tracking-wider text-ink hover:border-info"
        >
          ↓ Export JSON
        </button>
      </div>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 px-4 py-3 sm:grid-cols-3 lg:grid-cols-6">
        <Stat name="Last close" value={money(ev.current_price, ev.currency)} />
        <Stat name="Market cap" value={compact(ev.market_cap)} />
        <Stat name="Analyzed" value={dateTime(data.analyzed_at)} mono={false} />
        <Stat name="Run time" value={`${data.duration_seconds.toFixed(1)}s`} />
        <Stat name="Model" value={data.model ?? "—"} />
        <Stat name="Sessions" value={`${ev.history.length} daily`} />
      </dl>
      {ev.missing_fields.length > 0 && (
        <div className="border-t border-line px-4 py-2 text-xs text-ink-2">
          <span className="font-mono uppercase tracking-wider text-warn">◆ Missing evidence:</span>{" "}
          {ev.missing_fields.map(label).join(", ")}
          <span className="text-muted"> — not available from Yahoo Finance; agents were told these are missing, not zero.</span>
        </div>
      )}
    </section>
  );
}
