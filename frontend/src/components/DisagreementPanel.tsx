import type { AnalysisResponse } from "../lib/types";
import { label, levelTone, riskTone, stanceTone } from "../lib/format";
import { AgentList, Badge, Panel } from "./ui";

type Lane = "negative" | "none" | "positive";

function laneFor(status: string): Lane {
  if (status === "positive") return "positive";
  if (status === "negative") return "negative";
  return "none";
}

function roleFor(agent: string, status: string, data: AnalysisResponse): string {
  const d = data.disagreement;
  if (d.failed_agents.includes(agent)) return "Execution failed";
  if (d.evidence_gaps.includes(agent)) return "Insufficient evidence";
  if (d.conflicting_agents.includes(agent)) return "In conflict";
  if (agent === "risk") return "Context only (non-directional)";
  if (status === "positive" || status === "negative") return "Directional signal";
  return "No direction established";
}

export function DisagreementPanel({ data }: { data: AnalysisResponse }) {
  const d = data.disagreement;
  const dims = data.final_outlook.dimensions;
  const directional = (["valuation", "momentum"] as const).map((a) => ({ agent: a, status: dims[a], lane: laneFor(dims[a]) }));

  const lanes: { key: Lane; title: string; cls: string }[] = [
    { key: "negative", title: "Negative", cls: "text-neg" },
    { key: "none", title: "No direction", cls: "text-muted" },
    { key: "positive", title: "Positive", cls: "text-pos" },
  ];

  return (
    <Panel
      kicker="Consensus"
      title="Agreement & disagreement"
      right={<Badge value={d.classification} tone={levelTone(d.classification)} />}
    >
      <p className="text-sm text-ink-2">{d.explanation}</p>

      <div className="mt-4">
        <div className="mb-1.5 font-mono text-[11px] uppercase tracking-wider text-muted">Directional alignment</div>
        <div className="grid grid-cols-3 gap-px border border-line bg-line">
          {lanes.map((lane) => (
            <div key={lane.key} className="min-h-20 bg-panel-2 px-3 py-2">
              <div className={`font-mono text-[10px] uppercase tracking-wider ${lane.cls}`}>{lane.title}</div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {directional
                  .filter((x) => x.lane === lane.key)
                  .map((x) => (
                    <span
                      key={x.agent}
                      className="border border-line-strong bg-panel px-2 py-1 font-mono text-[11px] uppercase text-ink"
                      title={label(x.status)}
                    >
                      {x.agent}
                      {lane.key === "none" && <span className="ml-1 normal-case text-muted">({label(x.status)})</span>}
                    </span>
                  ))}
              </div>
            </div>
          ))}
        </div>
        <p className="mt-1.5 text-xs text-muted">
          Only valuation and momentum are directional. Risk ({label(dims.risk)}) is contextual and never placed on this axis.
        </p>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[420px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-line text-left font-mono text-[10px] uppercase tracking-wider text-muted">
              <th className="py-1.5 pr-3 font-normal">Agent</th>
              <th className="py-1.5 pr-3 font-normal">Result</th>
              <th className="py-1.5 font-normal">Role in synthesis</th>
            </tr>
          </thead>
          <tbody>
            {(["valuation", "risk", "momentum"] as const).map((agent) => (
              <tr key={agent} className="border-b border-line/60 last:border-0">
                <td className="py-2 pr-3 font-mono text-xs uppercase text-ink">{agent}</td>
                <td className="py-2 pr-3">
                  <Badge value={dims[agent]} tone={agent === "risk" ? riskTone(dims[agent]) : stanceTone(dims[agent])} />
                </td>
                <td className="py-2 text-xs text-ink-2">{roleFor(agent, dims[agent], data)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <dl className="mt-4 grid gap-2 sm:grid-cols-3">
        {(
          [
            ["Conflicting", d.conflicting_agents],
            ["Evidence gaps", d.evidence_gaps],
            ["Failed", d.failed_agents],
          ] as [string, string[]][]
        ).map(([k, v]) => (
          <div key={k} className="border border-line bg-panel-2 px-3 py-2">
            <dt className="font-mono text-[10px] uppercase tracking-wider text-muted">{k}</dt>
            <dd className="mt-1.5">
              <AgentList agents={v} />
            </dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}
