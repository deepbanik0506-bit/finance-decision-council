import { useState } from "react";
import type { AgentResult, AnalysisResponse, BaseAssessment } from "../lib/types";
import { compact, label, num, pct, riskTone, stanceTone, type Tone } from "../lib/format";
import { Badge, BulletList, Panel, SectionLabel, Stat } from "./ui";

type Metric = { name: string; value: string; hint?: string; missing?: boolean };

const TABS = ["evidence", "assumptions", "limitations", "reasoning"] as const;
type Tab = (typeof TABS)[number];

function AgentCard({
  title,
  description,
  result,
  signalName,
  signal,
  tone,
  metrics,
  metricsNote,
}: {
  title: string;
  description: string;
  result: AgentResult<BaseAssessment>;
  signalName: string;
  signal: string | null;
  tone: Tone;
  metrics: Metric[];
  metricsNote?: string;
}) {
  const [tab, setTab] = useState<Tab>("evidence");
  const a = result.assessment;
  const failed = result.status === "failed";

  return (
    <Panel
      kicker="Agent"
      title={title}
      right={
        <span className={`font-mono text-[11px] uppercase tracking-wider ${failed ? "text-neg" : "text-pos"}`}>
          {failed ? "▼ failed" : "▲ executed"}
        </span>
      }
      className="flex flex-col"
    >
      <p className="text-xs text-muted">{description}</p>

      <div className="mt-3 flex items-center justify-between gap-2 border border-line bg-panel-2 px-3 py-2">
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted">{signalName}</span>
        {failed ? <Badge value="failed" tone="neg" /> : <Badge value={signal ?? "unknown"} tone={tone} />}
      </div>

      <div className="mt-3">
        <SectionLabel>Inputs supplied to agent</SectionLabel>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2.5">
          {metrics.map((m) => (
            <Stat key={m.name} name={m.name} hint={m.hint} value={m.missing ? <span className="text-muted">missing</span> : m.value} />
          ))}
        </dl>
        {metricsNote && <p className="mt-2 text-xs text-muted">{metricsNote}</p>}
      </div>

      <div className="mt-4 border-t border-line pt-3">
        {failed || !a ? (
          <div className="border border-neg/30 bg-neg/5 px-3 py-2.5">
            <div className="font-mono text-[11px] uppercase tracking-wider text-neg">
              {label(result.failure?.category ?? "unknown")}
            </div>
            <p className="mt-1 text-sm text-ink-2">{result.failure?.message ?? "The agent did not return an assessment."}</p>
            <p className="mt-1 text-xs text-muted">
              The council recorded this dimension as failed. No assessment is shown for it.
            </p>
          </div>
        ) : (
          <>
            <div role="tablist" className="grid grid-cols-2 gap-px border border-line bg-line sm:grid-cols-4">
              {TABS.map((t) => {
                const count = t === "reasoning" ? null : a[t].length;
                return (
                  <button
                    key={t}
                    role="tab"
                    type="button"
                    aria-selected={tab === t}
                    onClick={() => setTab(t)}
                    className={`min-w-0 px-2 py-1.5 font-mono text-[10px] uppercase tracking-wider ${
                      tab === t ? "bg-panel-2 text-ink" : "bg-panel text-muted hover:text-ink-2"
                    }`}
                  >
                    {t}
                    {count !== null && <span className="ml-1 text-muted">{count}</span>}
                  </button>
                );
              })}
            </div>
            <div role="tabpanel" className="mt-3 min-h-24">
              {tab === "reasoning" ? (
                <p className="text-sm leading-relaxed text-ink-2">{a.reasoning || "No reasoning provided."}</p>
              ) : (
                <BulletList items={a[tab]} />
              )}
            </div>
          </>
        )}
      </div>
    </Panel>
  );
}

function metric(name: string, value: number | null, fmt: (v: number) => string, hint?: string): Metric {
  return { name, value: value === null ? "—" : fmt(value), hint, missing: value === null };
}

export function AgentPanels({ data }: { data: AnalysisResponse }) {
  const ev = data.market_evidence;
  const mi = data.momentum_indicators;
  const v = data.agents.valuation;
  const r = data.agents.risk;
  const m = data.agents.momentum;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <AgentCard
        title="Valuation"
        description="Interprets supplied valuation ratios without peer or historical benchmarks."
        result={v}
        signalName="Stance"
        signal={v.assessment?.stance ?? null}
        tone={stanceTone(v.assessment?.stance ?? "")}
        metrics={[
          metric("Trailing P/E", ev.trailing_pe, (x) => num(x)),
          metric("Price / Book", ev.price_to_book, (x) => num(x)),
          metric("EV / EBITDA", ev.enterprise_to_ebitda, (x) => num(x)),
          metric("Market cap", ev.market_cap, (x) => compact(x)),
        ]}
      />
      <AgentCard
        title="Risk"
        description="Assesses beta, leverage and one year of closing prices. Not statistically calibrated."
        result={r}
        signalName="Risk level"
        signal={r.assessment?.risk_level ?? null}
        tone={riskTone(r.assessment?.risk_level ?? "")}
        metrics={[
          metric("Beta", ev.beta, (x) => num(x), "Sensitivity to broad market moves"),
          metric("Debt / Equity", ev.debt_to_equity, (x) => num(x), "As reported by Yahoo Finance"),
          { name: "Price history", value: `${ev.history.length} sessions` },
          { name: "Sector", value: ev.sector ?? "—", missing: ev.sector === null },
        ]}
      />
      <AgentCard
        title="Momentum"
        description="Interprets deterministic moving-average, price-change and volume indicators."
        result={m}
        signalName="Stance"
        signal={m.assessment?.stance ?? null}
        tone={stanceTone(m.assessment?.stance ?? "")}
        metrics={
          mi
            ? [
                metric("MA 20", mi.ma_20, (x) => num(x)),
                metric("MA 50", mi.ma_50, (x) => num(x)),
                metric("MA 200", mi.ma_200, (x) => num(x), "Requires 200 sessions"),
                metric("Close", mi.current_close, (x) => num(x)),
                metric("20d change", mi.price_change_20d_pct, (x) => pct(x)),
                metric("50d change", mi.price_change_50d_pct, (x) => pct(x)),
                metric("Avg vol 20d", mi.average_volume_20d, (x) => compact(x)),
                metric("Latest vol", mi.latest_volume, (x) => compact(x)),
              ]
            : []
        }
        metricsNote={mi ? undefined : `Indicators unavailable: ${data.momentum_indicators_unavailable_reason ?? "unknown reason"}.`}
      />
    </div>
  );
}
