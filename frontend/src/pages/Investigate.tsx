import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Check,
  ChevronDown,
  Database,
  PenLine,
  Route,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { runInvestigation } from "../api";
import GroundedAnswer from "../components/GroundedAnswer";
import { Badge, EmptyState, ErrorState, PageHeader, Panel, Spinner } from "../components/ui";

const stages = [
  { name: "Planner", icon: Route, text: "Decomposing goal" },
  { name: "Data agent", icon: Database, text: "Running ML models" },
  { name: "Document agent", icon: ScanSearch, text: "Retrieving clauses" },
  { name: "Writer", icon: PenLine, text: "Recording evidence" },
  { name: "Checker", icon: ShieldCheck, text: "Validating claims" },
];

function Pipeline({ step, done, failed }: { step: number; done: boolean; failed: boolean }) {
  return (
    <div className="panel overflow-hidden">
      <div className="grid gap-3 sm:grid-cols-5">
        {stages.map((s, i) => {
          const complete = done || i < step;
          const active = !done && !failed && i === step;
          return (
            <div key={s.name} className="relative flex items-center gap-3 sm:flex-col sm:text-center">
              {i < stages.length - 1 && (
                <div className="absolute left-[calc(50%+28px)] right-[calc(-50%+28px)] top-6 hidden h-px bg-line sm:block">
                  <motion.div
                    className="h-full bg-gradient-to-r from-cyan to-violet"
                    initial={{ width: 0 }}
                    animate={{ width: complete ? "100%" : "0%" }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              )}
              <motion.div
                animate={{
                  scale: active ? [1, 1.08, 1] : 1,
                }}
                transition={{ duration: 1.2, repeat: active ? Infinity : 0 }}
                className={`relative z-10 grid h-12 w-12 shrink-0 place-items-center rounded-2xl ring-1 transition-colors duration-500 ${
                  complete
                    ? "bg-ok/15 text-ok ring-ok/30"
                    : active
                    ? "bg-cyan/15 text-cyan ring-cyan/40 shadow-glow"
                    : failed && i === step
                    ? "bg-risk/15 text-risk ring-risk/30"
                    : "bg-deep text-muted ring-line"
                }`}
              >
                <AnimatePresence mode="wait">
                  {complete ? (
                    <motion.span key="c" initial={{ scale: 0, rotate: -90 }} animate={{ scale: 1, rotate: 0 }}>
                      <Check size={20} />
                    </motion.span>
                  ) : failed && i === step ? (
                    <motion.span key="x" initial={{ scale: 0 }} animate={{ scale: 1 }}>
                      <X size={20} />
                    </motion.span>
                  ) : (
                    <motion.span key="i">
                      <s.icon size={20} />
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
              <div className="sm:mt-2">
                <p className={`text-sm font-semibold ${complete || active ? "text-fg" : "text-muted"}`}>{s.name}</p>
                <p className="font-mono text-[11px] text-muted">
                  {active ? (
                    <span className="text-cyan">
                      {s.text}
                      <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ duration: 1.2, repeat: Infinity }}>
                        …
                      </motion.span>
                    </span>
                  ) : complete ? (
                    "done"
                  ) : (
                    "queued"
                  )}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Fact({ label, value, tone }: { label: string; value: React.ReactNode; tone?: string }) {
  return (
    <div className="rounded-xl border border-line bg-deep/50 p-3">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-1 font-display text-lg font-semibold ${tone ?? ""}`}>{value ?? "—"}</p>
    </div>
  );
}

export default function Investigate() {
  const [orderId, setOrderId] = useState(1);
  const [query, setQuery] = useState("Investigate potential disruption and late delivery risk");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState(0);
  const [started, setStarted] = useState(false);
  const [raw, setRaw] = useState(false);

  useEffect(() => {
    if (!loading) return;
    const t = setInterval(() => setStep((s) => Math.min(s + 1, stages.length - 1)), 1100);
    return () => clearInterval(t);
  }, [loading]);

  async function run() {
    setLoading(true);
    setStarted(true);
    setError("");
    setResult(null);
    setStep(0);
    try {
      setResult(await runInvestigation(query, orderId));
    } catch (e: any) {
      setError(e.message || "Investigation failed");
    } finally {
      setLoading(false);
    }
  }

  const ml = result?.ml_findings || {};
  const checker = result?.checker_result || {};
  const checked = checker.checked ?? 0;
  const validated = checker.validated ?? 0;

  return (
    <>
      <PageHeader
        eyebrow="Layer C · Agentic AI"
        title="Agentic Investigation"
        description="Give SCOPE one goal. The agent graph plans, analyses, retrieves and verifies — then reports only what it can back up."
      />

      <Panel className="grid gap-3 md:grid-cols-[1fr_9rem_auto]">
        <div className="relative">
          <Sparkles size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan" />
          <input className="field pl-11" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Describe your goal…" />
        </div>
        <input
          className="field font-mono"
          type="number"
          value={orderId}
          onChange={(e) => setOrderId(Number(e.target.value))}
          aria-label="Order ID"
        />
        <button onClick={run} disabled={loading} className="btn-primary">
          {loading ? <Spinner label="Running…" /> : "Start investigation"}
        </button>
      </Panel>

      <AnimatePresence>
        {started && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-4">
            <Pipeline step={step} done={!!result} failed={!!error} />
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}

      {!started && (
        <Panel className="mt-4">
          <EmptyState
            icon={<Sparkles size={22} />}
            title="Ready when you are"
            text="Enter a goal and an order ID. You'll see each agent hand off to the next."
          />
        </Panel>
      )}

      {result && (
        <motion.div
          initial="hidden"
          animate="show"
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.1 } } }}
          className="mt-4 grid gap-4 lg:grid-cols-3"
        >
          <motion.div
            variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }}
            className="panel lg:row-span-2"
          >
            <div className="flex items-center justify-between">
              <p className="panel-title">Plan</p>
              <Badge tone="cyan">{result.status}</Badge>
            </div>
            <ol className="relative mt-4 space-y-4 border-l border-line pl-5">
              {(result.plan || []).map((p: string, i: number) => (
                <motion.li
                  key={p}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + i * 0.07 }}
                  className="relative text-sm"
                >
                  <span className="absolute -left-[27px] top-0.5 grid h-3.5 w-3.5 place-items-center rounded-full bg-void ring-1 ring-cyan/50">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan" />
                  </span>
                  <span className="mr-2 font-mono text-xs text-muted">{String(i + 1).padStart(2, "0")}</span>
                  {p}
                </motion.li>
              ))}
            </ol>
          </motion.div>

          <motion.div
            variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }}
            className="panel lg:col-span-2"
          >
            <p className="panel-title">ML findings</p>
            <p className="text-sm text-muted">
              {ml.vendor ?? "—"} · {ml.country ?? "—"} · {ml.shipment_mode ?? "—"}
            </p>
            <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
              <Fact
                label="Late probability"
                value={ml.late_probability != null ? `${(ml.late_probability * 100).toFixed(1)}%` : null}
                tone={ml.late_prediction ? "text-risk" : "text-ok"}
              />
              <Fact
                label="Predicted duration"
                value={ml.predicted_duration_days != null ? `${ml.predicted_duration_days.toFixed(1)} d` : null}
              />
              <Fact label="Anomaly score" value={ml.anomaly_score?.toFixed?.(3)} tone={ml.is_anomaly ? "text-warn" : ""} />
              <Fact
                label="Actual outcome"
                value={ml.actual_is_late == null ? "unknown" : ml.actual_is_late ? "Late" : "On-time"}
              />
            </div>
            {ml.duration_low_confidence && (
              <p className="mt-3 text-xs text-warn">Duration estimate is low-confidence (did not beat median baseline).</p>
            )}
          </motion.div>

          <motion.div
            variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }}
            className="panel lg:col-span-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="panel-title">Checker</p>
              <div className="flex gap-2">
                <Badge tone="ok">{validated} validated</Badge>
                {(checker.needs_review ?? 0) > 0 && <Badge tone="warn">{checker.needs_review} needs review</Badge>}
              </div>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/5">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-ok to-cyan"
                initial={{ width: 0 }}
                animate={{ width: checked ? `${(validated / checked) * 100}%` : "0%" }}
                transition={{ duration: 1, delay: 0.4 }}
              />
            </div>
            <ul className="mt-4 space-y-2">
              {(checker.results || []).map((r: any) => (
                <li key={r.evidence_id} className="flex items-start gap-3 text-sm">
                  {r.status === "validated" ? (
                    <Check size={16} className="mt-0.5 shrink-0 text-ok" />
                  ) : (
                    <X size={16} className="mt-0.5 shrink-0 text-warn" />
                  )}
                  <span className="font-mono text-xs text-muted">{String(r.evidence_id).slice(0, 8)}</span>
                  <span className="text-muted">{r.notes}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }}
            className="panel lg:col-span-3"
          >
            <p className="panel-title">Document findings</p>
            <div className="mt-4">
              <GroundedAnswer answer={result.document_findings?.answer ?? ""} compact />
            </div>
          </motion.div>
        </motion.div>
      )}

      {result && (
        <div className="mt-4">
          <button onClick={() => setRaw((s) => !s)} className="flex items-center gap-2 text-sm text-muted hover:text-fg">
            <motion.span animate={{ rotate: raw ? 180 : 0 }}>
              <ChevronDown size={16} />
            </motion.span>
            Raw response
          </button>
          <AnimatePresence>
            {raw && (
              <motion.pre
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="panel mt-2 max-h-96 overflow-auto font-mono text-xs text-muted"
              >
                {JSON.stringify(result, null, 2)}
              </motion.pre>
            )}
          </AnimatePresence>
        </div>
      )}
    </>
  );
}
