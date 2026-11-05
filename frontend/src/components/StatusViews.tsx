import { useEffect, useState } from "react";
import type { ApiRequestError } from "../lib/api";
import { label } from "../lib/format";

export function EmptyState() {
  const steps: [string, string][] = [
    ["Market data", "One year of daily prices plus available fundamentals are fetched from Yahoo Finance (yfinance). Missing fields are tracked, never filled in."],
    ["Three independent agents", "Valuation, Risk and Momentum agents (Groq-hosted LLMs) run in parallel. Each sees only its slice of the evidence and must state evidence, assumptions and limitations."],
    ["Deterministic synthesis", "Rule-based nodes detect disagreement, grade evidence quality, analytical agreement and execution reliability, then combine valuation and momentum into an outlook."],
  ];
  return (
    <div className="border border-line bg-panel">
      <div className="border-b border-line px-5 py-4">
        <h2 className="text-sm font-semibold text-ink">How the council works</h2>
        <p className="mt-1 text-sm text-ink-2">
          Enter a ticker to run the full council. The result shows each agent separately, where they agree or conflict,
          and how complete the evidence was. When the evidence does not support a direction, the council says so.
        </p>
      </div>
      <ol className="grid gap-px bg-line md:grid-cols-3">
        {steps.map(([title, body], i) => (
          <li key={title} className="bg-panel px-5 py-4">
            <div className="font-mono text-[11px] text-muted">0{i + 1}</div>
            <div className="mt-1 text-sm font-medium text-ink">{title}</div>
            <p className="mt-1 text-sm leading-relaxed text-ink-2">{body}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function LoadingState({ ticker, onCancel }: { ticker: string; onCancel: () => void }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const started = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div role="status" aria-live="polite" className="border border-line bg-panel">
      <div className="h-0.5 w-full overflow-hidden bg-line">
        <div className="h-full w-1/3 animate-[fdc-indeterminate_1.6s_ease-in-out_infinite] bg-info" />
      </div>
      <div className="flex flex-wrap items-start justify-between gap-4 px-5 py-5">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-info">Analysis running · {ticker}</div>
          <p className="mt-2 max-w-2xl text-sm text-ink-2">
            The backend is fetching market data and running the Valuation, Risk and Momentum agents in parallel, followed by
            the synthesis step. The API returns only when the whole council has finished, so per-agent progress is not
            shown. This usually takes several seconds and can take over a minute if the model provider is slow or the
            server is waking from idle.
          </p>
          <p className="mt-2 text-sm text-muted">No results are shown until the council completes.</p>
        </div>
        <div className="text-right">
          <div className="font-mono text-2xl tabular text-ink">{elapsed}s</div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted">elapsed</div>
          <button
            type="button"
            onClick={onCancel}
            className="mt-3 border border-line-strong px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-ink-2 hover:text-ink"
          >
            Stop waiting
          </button>
        </div>
      </div>
      <style>{`@keyframes fdc-indeterminate { 0% { transform: translateX(-100%); } 100% { transform: translateX(300%); } }`}</style>
    </div>
  );
}

const ERROR_TITLES: Record<string, string> = {
  invalid_request: "Invalid ticker",
  ticker_not_found: "Ticker not found",
  market_data_unavailable: "Market data unavailable",
  provider_rate_limited: "Model provider rate limit reached",
  rate_limited: "Too many requests",
  council_execution_failed: "Council execution failed",
  service_misconfigured: "Backend not configured",
  server_busy: "Server busy",
  network_error: "Backend unreachable",
  timeout: "Request timed out",
  frontend_misconfigured: "Frontend not configured",
  internal_error: "Server error",
};

export function ErrorState({ ticker, error, onRetry }: { ticker: string; error: ApiRequestError; onRetry: () => void }) {
  const { code, message, details } = error.body;
  const failures = details?.agent_failures;
  return (
    <div role="alert" className="border border-neg/40 bg-panel">
      <div className="flex flex-wrap items-start justify-between gap-4 px-5 py-4">
        <div className="min-w-0">
          <div className="font-mono text-[11px] uppercase tracking-wider text-neg">
            ▼ {ERROR_TITLES[code] ?? "Analysis failed"} · {ticker}
            {error.status ? ` · HTTP ${error.status}` : ""}
          </div>
          <p className="mt-2 text-sm text-ink">{message}</p>
          <p className="mt-1 text-sm text-muted">No analysis was produced, so no outlook is displayed.</p>
        </div>
        <button
          type="button"
          onClick={onRetry}
          className="border border-line-strong bg-panel-2 px-4 py-1.5 font-mono text-xs uppercase tracking-wider text-ink hover:border-info"
        >
          Retry {ticker}
        </button>
      </div>
      {failures && (
        <div className="border-t border-line px-5 py-3">
          <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted">Agent failures</div>
          <dl className="grid gap-2 sm:grid-cols-3">
            {Object.entries(failures).map(([agent, f]) => (
              <div key={agent} className="border border-line bg-panel-2 px-3 py-2">
                <dt className="font-mono text-xs uppercase text-ink">
                  {agent} · <span className="text-neg">{label(f.category)}</span>
                </dt>
                <dd className="mt-1 text-xs text-ink-2">{f.message}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}
