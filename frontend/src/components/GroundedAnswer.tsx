import { Fragment } from "react";
import { motion } from "framer-motion";
import { FileText, Info, Quote } from "lucide-react";
import { Badge } from "./ui";

/**
 * Parses the backend's grounded-answer text:
 *   "Grounded summary for query: <q>\n\n- <snippet> [file.md#chunk-N]\n- ...\n\nNote: ..."
 * and renders each retrieved passage as a readable card.
 */

type Block =
  | { kind: "heading"; level: number; text: string }
  | { kind: "bullets"; items: string[] }
  | { kind: "para"; text: string };

type Passage = {
  file: string;
  chunk: string | null;
  synthetic: boolean;
  title: string | null;
  blocks: Block[];
  truncatedStart: boolean;
};

function parseSnippet(raw: string): Omit<Passage, "file" | "chunk"> {
  let text = raw.trim();
  let synthetic = false;
  const truncatedStart = /^[a-z'"`,;:)\]]/.test(text);

  // Unbalanced bold markers from mid-chunk cuts: if the first "**" is a closer
  // (e.g. "nt:** 8") drop it, otherwise the dangling opener at the end goes.
  if ((text.match(/\*\*/g) || []).length % 2 === 1) {
    const first = text.indexOf("**");
    const isCloser = /^\*\*(\s|[.,;:)]|$)/.test(text.slice(first));
    text = isCloser
      ? text.slice(0, first) + text.slice(first + 2)
      : text.replace(/\*\*(?!.*\*\*)/, "");
  }
  text = text.replace(/\s*\.\.\.\s*$/, "…");
  if (truncatedStart) text = "…" + text;

  const parts = text.split(/\s{2,}/).map((p) => p.trim()).filter(Boolean);
  const blocks: Block[] = [];
  let title: string | null = null;

  for (let part of parts) {
    const h = part.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      const headingText = h[2].trim();
      if (/SYNTHETIC DOCUMENT/i.test(headingText)) {
        synthetic = true;
        continue;
      }
      if (!title) title = headingText;
      else blocks.push({ kind: "heading", level: h[1].length, text: headingText });
      continue;
    }
    // bullet runs: "- a - b - c" or numbered "1. a 2. b"
    if (/^-\s/.test(part) || /\s-\s\*\*/.test(part)) {
      part = part.replace(/^-\s+/, "");
      const items = part.split(/\s+-\s+(?=\S)/).map((s) => s.replace(/^-\s+/, "").trim()).filter(Boolean);
      blocks.push({ kind: "bullets", items });
      continue;
    }
    if (/^\d+\.\s/.test(part)) {
      const items = part.split(/\s(?=\d+\.\s)/).map((s) => s.trim());
      blocks.push({ kind: "bullets", items });
      continue;
    }
    blocks.push({ kind: "para", text: part });
  }

  return { synthetic, title, blocks, truncatedStart };
}

export function parseGroundedAnswer(answer: string) {
  const lines = (answer || "").split(/\r?\n/);
  let query: string | null = null;
  let note: string | null = null;
  const passages: Passage[] = [];
  const other: string[] = [];

  for (const line of lines) {
    const l = line.trim();
    if (!l) continue;
    const q = l.match(/^Grounded summary for query:\s*(.*)$/i);
    if (q) {
      query = q[1];
      continue;
    }
    if (/^Note:/i.test(l)) {
      note = l.replace(/^Note:\s*/i, "");
      continue;
    }
    if (l.startsWith("- ")) {
      let body = l.slice(2);
      const src = body.match(/\[([^\]\[]+?)\]\s*$/);
      let file = "source";
      let chunk: string | null = null;
      if (src) {
        body = body.slice(0, src.index).trim();
        const [f, c] = src[1].split("#");
        file = f;
        chunk = c?.replace(/^chunk-/, "") ?? null;
      }
      const parsed = parseSnippet(body);
      passages.push({ file, chunk, ...parsed, synthetic: parsed.synthetic || /synthetic/i.test(file) });
      continue;
    }
    other.push(l);
  }
  return { query, passages, note, other };
}

function Inline({ text }: { text: string }) {
  // **bold** and `code`
  const tokens = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return (
    <>
      {tokens.map((t, i) => {
        if (/^\*\*[^*]+\*\*$/.test(t)) return <strong key={i} className="font-semibold text-fg">{t.slice(2, -2)}</strong>;
        if (/^`[^`]+`$/.test(t))
          return (
            <code key={i} className="rounded bg-white/5 px-1 py-0.5 font-mono text-[12px] text-cyan-soft">
              {t.slice(1, -1)}
            </code>
          );
        return <Fragment key={i}>{t.replace(/\*\*/g, "")}</Fragment>;
      })}
    </>
  );
}

function PassageCard({ p, index }: { p: Passage; index: number }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08 * index, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="group relative rounded-xl border border-line bg-deep/50 p-4 transition hover:border-cyan/30"
    >
      <span className="absolute left-0 top-4 h-8 w-[3px] rounded-r bg-gradient-to-b from-cyan to-violet opacity-60 transition group-hover:opacity-100" />
      <header className="flex flex-wrap items-center gap-2">
        <span className="grid h-6 w-6 place-items-center rounded-md bg-cyan/10 font-mono text-[11px] text-cyan">
          {index + 1}
        </span>
        <span className="flex min-w-0 items-center gap-1.5 text-xs text-muted">
          <FileText size={13} className="shrink-0" />
          <span className="truncate font-mono">{p.file}</span>
          {p.chunk && <span className="font-mono text-muted/70">· chunk {p.chunk}</span>}
        </span>
        {p.synthetic && <Badge tone="warn">synthetic</Badge>}
      </header>

      {p.title && <h4 className="mt-3 font-display text-[15px] font-semibold leading-snug text-fg">{p.title}</h4>}

      <div className="mt-2 space-y-2 text-sm leading-relaxed text-fg/80">
        {p.blocks.map((b, i) => {
          if (b.kind === "heading")
            return (
              <p key={i} className="pt-1 font-mono text-[11px] uppercase tracking-wider text-violet-soft">
                <Inline text={b.text} />
              </p>
            );
          if (b.kind === "bullets")
            return (
              <ul key={i} className="space-y-1">
                {b.items.map((it, j) => (
                  <li key={j} className="flex gap-2">
                    <span className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-cyan/70" />
                    <span>
                      <Inline text={it} />
                    </span>
                  </li>
                ))}
              </ul>
            );
          return (
            <p key={i}>
              <Inline text={b.text} />
            </p>
          );
        })}
      </div>
    </motion.article>
  );
}

export default function GroundedAnswer({ answer, compact }: { answer: string; compact?: boolean }) {
  const { query, passages, note, other } = parseGroundedAnswer(answer);

  if (!passages.length)
    return <p className="whitespace-pre-wrap text-sm leading-relaxed text-fg/85">{answer || "—"}</p>;

  return (
    <div className="space-y-4">
      {query && (
        <div className="flex items-start gap-3 rounded-xl border border-line bg-white/[0.02] px-4 py-3">
          <Quote size={15} className="mt-0.5 shrink-0 text-cyan" />
          <div className="min-w-0">
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted">Query</p>
            <p className="mt-0.5 text-sm text-fg/90">{query}</p>
          </div>
        </div>
      )}
      {other.map((o, i) => (
        <p key={i} className="text-sm text-fg/85">
          <Inline text={o} />
        </p>
      ))}
      <div className="flex items-center justify-between">
        <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
          {passages.length} retrieved passage{passages.length === 1 ? "" : "s"}
        </p>
      </div>
      <div className={compact ? "grid gap-3 md:grid-cols-2" : "space-y-3"}>
        {passages.map((p, i) => (
          <PassageCard key={i} p={p} index={i} />
        ))}
      </div>
      {note && (
        <p className="flex items-start gap-2 text-xs text-muted">
          <Info size={13} className="mt-0.5 shrink-0 text-warn" />
          {note}
        </p>
      )}
    </div>
  );
}
