import { useCallback, useEffect, useRef, useState } from "react";
import { ApiRequestError, analyzeTicker, fetchHealth } from "./lib/api";
import type { AnalysisResponse } from "./lib/types";
import { Header, type HealthState } from "./components/Header";
import { TickerForm } from "./components/TickerForm";
import { EmptyState, ErrorState, LoadingState } from "./components/StatusViews";
import { ResultHeader } from "./components/ResultHeader";
import { OutlookPanel } from "./components/OutlookPanel";
import { AgentPanels } from "./components/AgentPanel";
import { DisagreementPanel } from "./components/DisagreementPanel";
import { PriceCharts } from "./components/PriceCharts";

export const DISCLAIMER =
  "Finance Decision Council is an analytical research prototype. Outputs are not personalized investment advice. Confidence scores are heuristic and do not represent probabilities of correctness.";

type View =
  | { kind: "idle" }
  | { kind: "loading"; ticker: string }
  | { kind: "success"; ticker: string; data: AnalysisResponse }
  | { kind: "error"; ticker: string; error: ApiRequestError };

export default function App() {
  const [health, setHealth] = useState<HealthState>({ kind: "checking" });
  const [view, setView] = useState<View>({ kind: "idle" });
  const inflight = useRef<AbortController | null>(null);

  const checkHealth = useCallback(() => {
    setHealth({ kind: "checking" });
    fetchHealth()
      .then((data) => setHealth({ kind: "ok", data }))
      .catch((err: unknown) =>
        setHealth({ kind: "down", message: err instanceof Error ? err.message : "Health check failed" }),
      );
  }, []);

  useEffect(() => {
    checkHealth();
    return () => inflight.current?.abort();
  }, [checkHealth]);

  const run = useCallback((ticker: string) => {
    if (inflight.current) return; // prevent duplicate submissions
    const controller = new AbortController();
    inflight.current = controller;
    setView({ kind: "loading", ticker });

    analyzeTicker(ticker, controller.signal)
      .then((data) => setView({ kind: "success", ticker, data }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const error =
          err instanceof ApiRequestError
            ? err
            : new ApiRequestError(0, { code: "unknown", message: "An unexpected error occurred." });
        setView({ kind: "error", ticker, error });
      })
      .finally(() => {
        if (inflight.current === controller) inflight.current = null;
      });
  }, []);

  const cancel = useCallback(() => {
    inflight.current?.abort();
    inflight.current = null;
    setView({ kind: "idle" });
  }, []);

  const busy = view.kind === "loading";

  return (
    <div className="min-h-screen">
      <Header health={health} onRecheck={checkHealth} />

      <main className="mx-auto max-w-7xl space-y-4 px-4 py-5 sm:px-6">
        <section className="flex flex-col gap-4 border border-line bg-panel px-4 py-4 md:flex-row md:items-end md:justify-between">
          <div className="w-full md:max-w-md">
            <TickerForm busy={busy} onSubmit={run} />
          </div>
          <p className="max-w-xl text-xs leading-relaxed text-muted md:text-right">
            One ticker per run. Each run makes three language-model calls on the server, so requests are rate limited.
            Exchange suffixes follow Yahoo Finance (e.g. <span className="font-mono text-ink-2">SHOP.TO</span>,{" "}
            <span className="font-mono text-ink-2">RELIANCE.NS</span>).
          </p>
        </section>

        {view.kind === "idle" && <EmptyState />}
        {view.kind === "loading" && <LoadingState ticker={view.ticker} onCancel={cancel} />}
        {view.kind === "error" && <ErrorState ticker={view.ticker} error={view.error} onRetry={() => run(view.ticker)} />}
        {view.kind === "success" && (
          <div className="space-y-4">
            <ResultHeader data={view.data} />
            <OutlookPanel data={view.data} />
            <AgentPanels data={view.data} />
            <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)]">
              <DisagreementPanel data={view.data} />
              <PriceCharts evidence={view.data.market_evidence} />
            </div>
          </div>
        )}

        <footer className="border-t border-line pt-4 pb-8">
          <p className="border-l-2 border-warn/60 pl-3 text-xs leading-relaxed text-ink-2">
            <span className="font-medium text-warn">Disclaimer.</span> {DISCLAIMER}
          </p>
          <p className="mt-2 pl-3 text-xs text-muted">
            Market data: Yahoo Finance via yfinance. Agent analysis: language models hosted on Groq, interpreting only the
            supplied evidence. No news, analyst reports or peer benchmarks are used.
          </p>
        </footer>
      </main>
    </div>
  );
}
