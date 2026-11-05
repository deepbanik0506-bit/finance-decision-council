import type { ReactNode } from "react";
import { label, type Tone } from "../lib/format";

const toneText: Record<Tone, string> = {
  pos: "text-pos",
  neg: "text-neg",
  warn: "text-warn",
  info: "text-info",
  muted: "text-muted",
};

const toneBorder: Record<Tone, string> = {
  pos: "border-pos/40 bg-pos/10",
  neg: "border-neg/40 bg-neg/10",
  warn: "border-warn/40 bg-warn/10",
  info: "border-info/40 bg-info/10",
  muted: "border-line-strong bg-panel-2",
};

// Shape glyphs so state is never conveyed by color alone.
const toneGlyph: Record<Tone, string> = {
  pos: "▲",
  neg: "▼",
  warn: "◆",
  info: "●",
  muted: "○",
};

export function Panel({
  title,
  kicker,
  right,
  children,
  className = "",
}: {
  title?: ReactNode;
  kicker?: ReactNode;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`min-w-0 border border-line bg-panel ${className}`}>
      {(title || right) && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-2.5">
          <div className="flex min-w-0 items-baseline gap-2">
            {kicker && <span className="font-mono text-[11px] uppercase tracking-wider text-muted">{kicker}</span>}
            {title && <h2 className="truncate text-sm font-semibold tracking-wide text-ink">{title}</h2>}
          </div>
          {right}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function Badge({ value, tone, glyph = true, size = "sm" }: { value: string; tone: Tone; glyph?: boolean; size?: "sm" | "lg" }) {
  const sizing = size === "lg" ? "px-3 py-1.5 text-base" : "px-2 py-0.5 text-[11px]";
  return (
    <span
      className={`inline-flex items-center gap-1.5 border font-mono font-medium uppercase tracking-wider ${sizing} ${toneBorder[tone]} ${toneText[tone]}`}
    >
      {glyph && <span aria-hidden="true">{toneGlyph[tone]}</span>}
      {label(value)}
    </span>
  );
}

export function Stat({ name, value, mono = true, hint }: { name: string; value: ReactNode; mono?: boolean; hint?: string }) {
  return (
    <div className="min-w-0">
      <dt className="font-mono text-[10px] uppercase tracking-wider text-muted" title={hint}>
        {name}
      </dt>
      <dd className={`mt-0.5 truncate text-sm text-ink ${mono ? "font-mono tabular" : ""}`}>{value}</dd>
    </div>
  );
}

export function BulletList({ items, empty = "None reported by the agent." }: { items: string[]; empty?: string }) {
  if (!items.length) return <p className="text-sm italic text-muted">{empty}</p>;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2 text-sm leading-relaxed text-ink-2">
          <span aria-hidden="true" className="mt-[7px] h-1 w-1 shrink-0 bg-muted" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return <h3 className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted">{children}</h3>;
}

export function AgentList({ agents, empty = "none" }: { agents: string[]; empty?: string }) {
  if (!agents.length) return <span className="font-mono text-xs text-muted">{empty}</span>;
  return (
    <span className="flex flex-wrap gap-1">
      {agents.map((a) => (
        <span key={a} className="border border-line-strong bg-panel-2 px-1.5 py-0.5 font-mono text-[11px] uppercase text-ink-2">
          {a}
        </span>
      ))}
    </span>
  );
}
