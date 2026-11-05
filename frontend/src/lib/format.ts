export type Tone = "pos" | "neg" | "warn" | "info" | "muted";

export function label(value: string | null | undefined): string {
  if (!value) return "—";
  return value.replace(/_/g, " ");
}

export function titleCase(value: string): string {
  return label(value).replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Tone for directional stances and the overall outlook. */
export function stanceTone(value: string): Tone {
  switch (value) {
    case "positive":
      return "pos";
    case "negative":
      return "neg";
    case "mixed":
    case "partial_directional":
      return "warn";
    case "failed":
      return "neg";
    case "neutral":
      return "info";
    default:
      return "muted";
  }
}

/** Tone for risk level: higher risk is a caution, not a negative direction. */
export function riskTone(value: string): Tone {
  switch (value) {
    case "low":
      return "pos";
    case "moderate":
      return "warn";
    case "high":
      return "neg";
    case "failed":
      return "neg";
    default:
      return "muted";
  }
}

/** Tone for categorical quality/reliability/agreement levels. */
export function levelTone(value: string): Tone {
  switch (value) {
    case "complete":
    case "aligned":
    case "no_conflict":
      return "pos";
    case "partial":
    case "limited":
    case "evidence_gap":
      return "warn";
    case "poor":
    case "failed":
    case "conflicting":
    case "conflict":
    case "agent_failure":
      return "neg";
    default:
      return "muted";
  }
}

export function num(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function pct(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

export function compact(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(value);
}

export function money(value: number | null | undefined, currency: string | null): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const formatted = num(value, 2);
  return currency ? `${formatted} ${currency}` : formatted;
}

export function dateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function shortDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "2-digit" });
}
