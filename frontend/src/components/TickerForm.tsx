import { useState, type FormEvent } from "react";
import { TICKER_PATTERN } from "../lib/api";

export function TickerForm({
  busy,
  onSubmit,
  initial = "",
}: {
  busy: boolean;
  onSubmit: (ticker: string) => void;
  initial?: string;
}) {
  const [value, setValue] = useState(initial);
  const [error, setError] = useState<string | null>(null);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    const ticker = value.trim().toUpperCase();
    if (!ticker) {
      setError("Enter a ticker symbol.");
      return;
    }
    if (!TICKER_PATTERN.test(ticker)) {
      setError("Use 1–10 characters: letters, digits, '.' or '-' (e.g. AAPL, BRK-B, RELIANCE.NS).");
      return;
    }
    setError(null);
    setValue(ticker);
    onSubmit(ticker);
  }

  return (
    <form onSubmit={submit} noValidate className="w-full">
      <label htmlFor="ticker" className="mb-1.5 block font-mono text-[11px] uppercase tracking-wider text-muted">
        Ticker symbol
      </label>
      <div className="flex w-full gap-2">
        <div className="relative flex-1">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 font-mono text-sm text-muted">$</span>
          <input
            id="ticker"
            value={value}
            onChange={(e) => {
              setValue(e.target.value.toUpperCase());
              if (error) setError(null);
            }}
            disabled={busy}
            maxLength={10}
            autoComplete="off"
            autoCapitalize="characters"
            spellCheck={false}
            placeholder="AAPL"
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? "ticker-error" : undefined}
            className="h-11 w-full border border-line-strong bg-panel-2 pl-7 pr-3 font-mono text-base uppercase tracking-wider text-ink placeholder:text-muted/60 focus:border-info focus:outline-none disabled:opacity-60"
          />
        </div>
        <button
          type="submit"
          disabled={busy}
          className="h-11 shrink-0 border border-info bg-info/15 px-5 font-mono text-sm font-medium uppercase tracking-wider text-ink hover:bg-info/25 disabled:cursor-not-allowed disabled:border-line-strong disabled:bg-panel-2 disabled:text-muted"
        >
          {busy ? "Running…" : "Analyze"}
        </button>
      </div>
      {error && (
        <p id="ticker-error" role="alert" className="mt-1.5 text-xs text-neg">
          {error}
        </p>
      )}
    </form>
  );
}
