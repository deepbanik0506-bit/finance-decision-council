import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MarketEvidence, OHLCV } from "../lib/types";
import { compact, dateTime, num, pct, shortDate } from "../lib/format";
import { Panel } from "./ui";

const RANGES = [
  { key: "1M", sessions: 21 },
  { key: "3M", sessions: 63 },
  { key: "6M", sessions: 126 },
  { key: "1Y", sessions: Infinity },
] as const;
type RangeKey = (typeof RANGES)[number]["key"];

const AXIS = { stroke: "#2f3843", tick: { fill: "#7d8794", fontSize: 11, fontFamily: "IBM Plex Mono" } };
const GRID = "#1c232b";

function Crosshair({ active, payload }: { active?: boolean; payload?: ReadonlyArray<{ payload: OHLCV }> }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  const items: [string, string][] = [
    ["Open", num(row.open)],
    ["High", num(row.high)],
    ["Low", num(row.low)],
    ["Close", num(row.close)],
    ["Volume", compact(row.volume)],
  ];
  return (
    <div className="border border-line-strong bg-bg/95 px-3 py-2 font-mono text-xs shadow-lg">
      <div className="mb-1 text-ink">{row.date}</div>
      <dl className="grid grid-cols-[auto_auto] gap-x-4 gap-y-0.5 tabular">
        {items.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-muted">{k}</dt>
            <dd className="text-right text-ink">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function PriceCharts({ evidence }: { evidence: MarketEvidence }) {
  const [range, setRange] = useState<RangeKey>("1Y");
  const [showTable, setShowTable] = useState(false);

  const all = evidence.history;
  const rows = useMemo(() => {
    const n = RANGES.find((r) => r.key === range)!.sessions;
    return Number.isFinite(n) ? all.slice(-n) : all;
  }, [all, range]);

  // Dates that open the momentum agent's 20- and 50-session windows
  // (calculate_momentum_indicators uses the last 20/50 valid closes).
  const closes = all.filter((r) => r.close !== null);
  const window20 = closes.length >= 20 ? closes[closes.length - 20].date : null;
  const window50 = closes.length >= 50 ? closes[closes.length - 50].date : null;
  const inView = (d: string | null) => d !== null && rows.some((r) => r.date === d);

  const first = rows.find((r) => r.close !== null)?.close ?? null;
  const last = [...rows].reverse().find((r) => r.close !== null)?.close ?? null;
  const change = first && last ? (last / first - 1) * 100 : null;

  if (!all.length) {
    return (
      <Panel kicker="Market data" title="Price history">
        <p className="text-sm text-muted">No price history was returned.</p>
      </Panel>
    );
  }

  return (
    <Panel
      kicker="Market data"
      title={`Price history · ${evidence.ticker}`}
      right={
        <div className="flex items-center gap-px border border-line bg-line">
          {RANGES.map((r) => (
            <button
              key={r.key}
              type="button"
              onClick={() => setRange(r.key)}
              aria-pressed={range === r.key}
              className={`px-2.5 py-1 font-mono text-[11px] ${range === r.key ? "bg-panel-2 text-ink" : "bg-panel text-muted hover:text-ink-2"}`}
            >
              {r.key}
            </button>
          ))}
        </div>
      }
    >
      <div className="mb-3 flex flex-wrap items-baseline gap-x-6 gap-y-1 font-mono text-xs tabular">
        <span className="text-muted">
          Close <span className="text-ink">{num(last)}</span>
          {evidence.currency && <span className="ml-1 text-muted">{evidence.currency}</span>}
        </span>
        <span className="text-muted">
          Range change{" "}
          <span className={change === null ? "text-muted" : change >= 0 ? "text-pos" : "text-neg"}>{pct(change)}</span>
        </span>
        <span className="text-muted">
          {rows[0]?.date} → {rows[rows.length - 1]?.date} · {rows.length} sessions
        </span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} syncId="fdc" margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis dataKey="date" {...AXIS} tickFormatter={shortDate} minTickGap={40} hide />
            <YAxis {...AXIS} domain={["auto", "auto"]} width={60} tickFormatter={(v: number) => num(v, v >= 1000 ? 0 : 2)} orientation="right" />
            <Tooltip content={<Crosshair />} cursor={{ stroke: "#7d8794", strokeDasharray: "3 3" }} isAnimationActive={false} />
            {inView(window50) && (
              <ReferenceLine x={window50!} stroke="#7d8794" strokeDasharray="2 4" label={{ value: "50 sessions", position: "insideTopLeft", fill: "#7d8794", fontSize: 10 }} />
            )}
            {inView(window20) && (
              <ReferenceLine x={window20!} stroke="#7d8794" strokeDasharray="2 4" label={{ value: "20 sessions", position: "insideBottomLeft", fill: "#7d8794", fontSize: 10 }} />
            )}
            <Line
              type="linear"
              dataKey="close"
              stroke="var(--color-chart-line)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, stroke: "#11151a", strokeWidth: 2 }}
              connectNulls={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-1 font-mono text-[10px] uppercase tracking-wider text-muted">Volume</div>
      <div className="h-24 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} syncId="fdc" margin={{ top: 4, right: 8, bottom: 0, left: 0 }} barCategoryGap={1}>
            <XAxis dataKey="date" {...AXIS} tickFormatter={shortDate} minTickGap={40} />
            <YAxis {...AXIS} width={60} tickFormatter={(v: number) => compact(v)} orientation="right" tickCount={3} />
            <Tooltip content={<Crosshair />} cursor={{ fill: "#ffffff0d" }} isAnimationActive={false} />
            <Bar dataKey="volume" fill="var(--color-chart-volume)" isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-line pt-2">
        <p className="text-xs text-muted">
          Daily OHLCV from Yahoo Finance via yfinance, exactly as supplied to the council (fetched{" "}
          {dateTime(evidence.fetched_at)}). Dotted lines mark the start of the momentum agent's 20- and
          50-session windows.
        </p>
        <button
          type="button"
          onClick={() => setShowTable((s) => !s)}
          className="border border-line px-2 py-0.5 font-mono text-[11px] uppercase tracking-wider text-ink-2 hover:text-ink"
        >
          {showTable ? "Hide table" : "Show table"}
        </button>
      </div>

      {showTable && (
        <div className="mt-2 max-h-72 overflow-auto border border-line">
          <table className="w-full text-right font-mono text-xs tabular">
            <thead className="sticky top-0 bg-panel-2 text-muted">
              <tr>
                {["Date", "Open", "High", "Low", "Close", "Volume"].map((h) => (
                  <th key={h} className={`px-3 py-1.5 font-normal ${h === "Date" ? "text-left" : ""}`}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...rows].reverse().map((r) => (
                <tr key={r.date} className="border-t border-line/60 text-ink-2">
                  <td className="px-3 py-1 text-left">{r.date}</td>
                  <td className="px-3 py-1">{num(r.open)}</td>
                  <td className="px-3 py-1">{num(r.high)}</td>
                  <td className="px-3 py-1">{num(r.low)}</td>
                  <td className="px-3 py-1 text-ink">{num(r.close)}</td>
                  <td className="px-3 py-1">{compact(r.volume)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
