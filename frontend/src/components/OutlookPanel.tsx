import type { AnalysisResponse } from "../lib/types";
import { levelTone, riskTone, stanceTone, titleCase } from "../lib/format";
import { AgentList, Badge, Panel } from "./ui";

const OUTLOOK_COPY: Record<string, string> = {
  positive: "Valuation and momentum both point positive.",
  negative: "Valuation and momentum both point negative.",
  mixed: "Valuation and momentum point in opposite directions.",
  partial_directional: "Only one directional dimension established a direction.",
  insufficient_evidence: "The evidence did not support a directional conclusion.",
};

function Indicator({
  name,
  level,
  explanation,
  rows,
}: {
  name: string;
  level: string;
  explanation: string;
  rows: [string, string[]][];
}) {
  return (
    <div className="bg-panel px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted">{name}</span>
        <Badge value={level} tone={levelTone(level)} />
      </div>
      <p className="mt-2 text-xs leading-relaxed text-ink-2">{explanation}</p>
      <dl className="mt-2 space-y-1.5">
        {rows.map(([k, v]) => (
          <div key={k} className="flex flex-col gap-1">
            <dt className="text-xs text-muted">{k}</dt>
            <dd>
              <AgentList agents={v} />
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function OutlookPanel({ data }: { data: AnalysisResponse }) {
  const fo = data.final_outlook;
  const eq = data.evidence_quality;
  const ag = data.analytical_agreement;
  const ex = data.execution_reliability;

  return (
    <Panel kicker="Synthesis" title="Final council outlook">
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted">Overall outlook</div>
          <div className="mt-2">
            <Badge value={fo.overall_outlook} tone={stanceTone(fo.overall_outlook)} size="lg" />
          </div>
          <p className="mt-3 text-sm text-ink">{OUTLOOK_COPY[fo.overall_outlook] ?? titleCase(fo.overall_outlook)}</p>
          <p className="mt-1 text-sm text-ink-2">{fo.interpretation}</p>

          <div className="mt-4 grid grid-cols-3 gap-px border border-line bg-line">
            {(["valuation", "risk", "momentum"] as const).map((dim) => {
              const v = fo.dimensions[dim];
              return (
                <div key={dim} className="bg-panel-2 px-3 py-2">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-muted">{dim}</div>
                  <div className="mt-1">
                    <Badge value={v} tone={dim === "risk" ? riskTone(v) : stanceTone(v)} />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="mt-2 text-xs text-muted">
            The outlook combines valuation and momentum only. Risk is reported as separate context and does not set direction.
          </p>
        </div>

        <div>
          <div className="mb-2 border-l-2 border-warn/60 bg-warn/5 px-3 py-2 text-xs leading-relaxed text-ink-2">
            <span className="font-medium text-warn">Heuristic confidence.</span> The council does not produce a numeric
            confidence score or probability. Confidence is expressed through the three categorical indicators below, which
            describe evidence coverage, directional agreement and execution success. They do not represent the probability
            that the outlook is correct.
          </div>
          <div className="grid gap-px border border-line bg-line md:grid-cols-3">
            <Indicator
              name="Evidence quality"
              level={eq.level}
              explanation={eq.explanation}
              rows={[
                ["Usable", eq.usable_dimensions],
                ["Insufficient", eq.insufficient_dimensions],
                ["Failed", eq.failed_dimensions],
              ]}
            />
            <Indicator
              name="Analytical agreement"
              level={ag.classification}
              explanation={ag.explanation}
              rows={[
                ["Directional", ag.directional_agents],
                ["Positive", ag.positive_agents],
                ["Negative", ag.negative_agents],
              ]}
            />
            <Indicator
              name="Execution reliability"
              level={ex.reliability}
              explanation={ex.explanation}
              rows={[
                ["Succeeded", ex.successful_agents],
                ["Failed", ex.failed_agents],
              ]}
            />
          </div>
        </div>
      </div>
    </Panel>
  );
}
