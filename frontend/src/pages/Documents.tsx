import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BookOpenText, FileText, Info, Search } from "lucide-react";
import { ragQuery } from "../api";
import GroundedAnswer from "../components/GroundedAnswer";
import { Badge, EmptyState, ErrorState, PageHeader, Panel, Skeleton, Spinner } from "../components/ui";

const suggestions = [
  "vendor late delivery escalation policy",
  "penalty for late shipments",
  "lead-time limits for air freight",
];

export default function Documents() {
  const [query, setQuery] = useState("vendor late delivery escalation policy");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask(q = query) {
    setLoading(true);
    setError("");
    try {
      setResult(await ragQuery(q));
    } catch (e: any) {
      setError(e.message || "Retrieval failed");
    } finally {
      setLoading(false);
    }
  }

  const citations: any[] = result?.citations || [];
  const maxScore = Math.max(0.0001, ...citations.map((c) => c.score ?? 0));

  return (
    <>
      <PageHeader
        eyebrow="Layer B · Hybrid RAG"
        title="Document Intelligence"
        description="Ask a question across contracts, SLAs and policies. Answers are grounded in retrieved passages with citations."
      />

      <div className="mb-4 flex items-start gap-3 rounded-xl border border-warn/20 bg-warn/[0.06] px-4 py-3 text-sm text-warn">
        <Info size={16} className="mt-0.5 shrink-0" />
        Synthetic development documents are labelled and must not be treated as real contracts.
      </div>

      <Panel>
        <div className="relative">
          <Search size={16} className="absolute left-4 top-4 text-muted" />
          <textarea
            className="field resize-none pl-11"
            rows={3}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) ask();
            }}
          />
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => {
                  setQuery(s);
                  ask(s);
                }}
                className="rounded-full border border-line px-3 py-1 text-xs text-muted transition hover:border-cyan/40 hover:text-fg"
              >
                {s}
              </button>
            ))}
          </div>
          <button onClick={() => ask()} disabled={loading} className="btn-primary">
            {loading ? <Spinner label="Retrieving…" /> : (<><BookOpenText size={15} /> Retrieve grounded answer</>)}
          </button>
        </div>
      </Panel>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}

      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div key="loading" exit={{ opacity: 0 }} className="mt-4 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <Skeleton className="h-72" />
            <Skeleton className="h-72" />
          </motion.div>
        ) : result ? (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 grid gap-4 lg:grid-cols-[1.4fr_1fr]"
          >
            <div className="panel">
              <p className="panel-title">Grounded answer</p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Badge tone="cyan">{result.retrieval_mode || "retrieval mode unknown"}</Badge>
                <span className="text-xs text-muted">
                  Active: {(result.retrieval_components || []).join(" + ") || "no retriever"}
                </span>
              </div>
              <div className="mt-4">
                <GroundedAnswer answer={result.answer} />
              </div>
            </div>
            <div className="panel">
              <p className="panel-title">Citations</p>
              <ul className="mt-3 space-y-2">
                {citations.map((c, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + i * 0.08 }}
                    className="rounded-xl border border-line bg-deep/60 p-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="flex min-w-0 items-center gap-2 text-sm">
                        <FileText size={14} className="shrink-0 text-cyan" />
                        <span className="truncate">{c.file_name}</span>
                      </span>
                      {c.synthetic && <Badge tone="warn">synthetic</Badge>}
                    </div>
                    <div className="mt-2 flex items-center gap-3">
                      <span className="font-mono text-[11px] text-muted">chunk {c.page}</span>
                      <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                        <motion.div
                          className="h-full bg-gradient-to-r from-cyan to-violet"
                          initial={{ width: 0 }}
                          animate={{ width: `${((c.score ?? 0) / maxScore) * 100}%` }}
                          transition={{ duration: 0.8, delay: 0.2 + i * 0.08 }}
                        />
                      </div>
                      <span className="font-mono text-[11px] tabular-nums text-muted">{c.score?.toFixed?.(3)}</span>
                    </div>
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.div>
        ) : (
          <Panel className="mt-4">
            <EmptyState
              icon={<BookOpenText size={22} />}
              title="Ask the document corpus"
              text="Each answer reports which retrieval components were active for that query."
            />
          </Panel>
        )}
      </AnimatePresence>
    </>
  );
}
