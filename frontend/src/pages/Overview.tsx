import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  BookOpenText,
  Bot,
  CheckCircle2,
  Clock,
  Database,
  FileText,
  Layers,
  Microscope,
  PenLine,
  Route,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Unlock,
  Users,
} from "lucide-react";
import NetworkHero from "../components/NetworkHero";
import { CountUp, fadeUp, stagger } from "../components/ui";
import { getDashboard } from "../api";

const goals = [
  "Identify suppliers likely to cause disruption next month",
  "Which air shipments to West Africa are at risk of arriving late?",
  "Summarise penalty clauses for vendors flagged as anomalous",
];

function Typewriter() {
  const [i, setI] = useState(0);
  const [text, setText] = useState("");
  useEffect(() => {
    const full = goals[i];
    if (text.length < full.length) {
      const t = setTimeout(() => setText(full.slice(0, text.length + 1)), 32);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => {
      setText("");
      setI((i + 1) % goals.length);
    }, 2600);
    return () => clearTimeout(t);
  }, [text, i]);
  return (
    <span className="font-mono text-[13px] text-fg/90">
      {text}
      <span className="ml-0.5 inline-block h-4 w-[7px] translate-y-[3px] animate-pulse bg-cyan" />
    </span>
  );
}

function Section({
  id,
  eyebrow,
  title,
  text,
  children,
}: {
  id?: string;
  eyebrow: string;
  title: string;
  text?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24 py-16 sm:py-24">
      <motion.div
        variants={stagger}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        className="mx-auto mb-12 max-w-2xl text-center"
      >
        <motion.p variants={fadeUp} className="eyebrow">
          {eyebrow}
        </motion.p>
        <motion.h2
          variants={fadeUp}
          className="mt-3 font-display text-3xl font-semibold tracking-tight sm:text-4xl"
        >
          {title}
        </motion.h2>
        {text && (
          <motion.p variants={fadeUp} className="mt-4 text-[15px] leading-relaxed text-muted">
            {text}
          </motion.p>
        )}
      </motion.div>
      {children}
    </section>
  );
}

const layers = [
  {
    tag: "Layer A",
    title: "Machine Learning",
    icon: BarChart3,
    color: "from-cyan/30",
    accent: "text-cyan",
    items: [
      "Late-delivery risk — XGBoost vs. logistic baseline",
      "Demand forecasting — Prophet / ARIMA",
      "Anomaly detection — Isolation Forest on supplier KPIs",
      "Inventory stockout risk — experimental Random Forest proxy",
      "Supplier segmentation — K-Means",
      "Explainability — SHAP feature attributions",
    ],
  },
  {
    tag: "Layer B",
    title: "Hybrid RAG",
    icon: BookOpenText,
    color: "from-violet/30",
    accent: "text-violet-soft",
    items: [
      "Contracts & policies chunked with supplier metadata",
      "Dense vector search + BM25 keyword search",
      "Reciprocal Rank Fusion merge",
      "Cross-encoder reranking",
      "Clauses linked to suppliers flagged by Layer A",
    ],
  },
  {
    tag: "Layer C",
    title: "Agentic AI",
    icon: Bot,
    color: "from-ok/30",
    accent: "text-ok",
    items: [
      "Stateful LangGraph agent graph",
      "JSON-schema tool calls",
      "Planner → Data → Document → Writer → Checker",
      "Evidence Ledger for every finding",
      "Claims labelled supported / corrected / unsupported",
    ],
  },
];

const agents = [
  { name: "Planner", icon: Route, text: "Decomposes the goal into ordered sub-tasks" },
  { name: "Data", icon: Database, text: "Calls ML tools, returns metrics & predictions" },
  { name: "Document", icon: ScanSearch, text: "Calls RAG, returns cited clause text" },
  { name: "Writer", icon: PenLine, text: "Drafts the report from stored findings only" },
  { name: "Checker", icon: ShieldCheck, text: "Validates every claim against the ledger" },
];

const comparisons = [
  { name: "BI dashboards", sub: "Power BI, Excel", gap: "Manual root-cause, no prediction, no documents" },
  { name: "Standalone ML", sub: "Classifiers, forecasters", gap: "A score with no explanation or contract link" },
  { name: "LLM over a CSV", sub: "Chat interfaces", gap: "Hallucinated figures, no evidence trail" },
  { name: "Enterprise suites", sub: "SAP IBP, Resilinc", gap: "Expensive, closed, hard to study" },
];

const values = [
  { icon: Clock, title: "Earlier detection", text: "Disruption risk is flagged before stockouts happen." },
  { icon: CheckCircle2, title: "Verifiable output", text: "Every claim traces to a computed value or document passage." },
  { icon: Layers, title: "Multi-modal analysis", text: "Tabular data and unstructured text analysed in one workflow." },
  { icon: Sparkles, title: "Lower analyst effort", text: "One natural-language goal replaces many manual steps." },
  { icon: Unlock, title: "Open & reproducible", text: "Open-source stack with baselines and ground-truth tests." },
  { icon: Microscope, title: "Research value", text: "ML, hybrid RAG and verified agents — with measured results." },
];

const team = [
  ["Amna Naveed", "2024-DS-42"],
  ["Zartashia Naz", "2024-DS-13"],
  ["Seerat Fatima", "2024-DS-32"],
  ["Aleena Ahmad", "2024-DS-09"],
];

function AgentFlow() {
  const [active, setActive] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setActive((a) => (a + 1) % agents.length), 1600);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="panel overflow-hidden p-6 sm:p-8">
      <div className="relative grid gap-4 md:grid-cols-5">
        <div className="absolute left-[10%] right-[10%] top-7 hidden h-px bg-line md:block" />
        <motion.div
          className="absolute left-[10%] top-7 hidden h-px bg-gradient-to-r from-cyan to-violet md:block"
          animate={{ width: `${(active / (agents.length - 1)) * 80}%` }}
          transition={{ duration: 0.6, ease: "easeInOut" }}
        />
        {agents.map((a, i) => {
          const on = i <= active;
          const current = i === active;
          return (
            <div key={a.name} className="relative flex items-start gap-4 md:flex-col md:items-center md:text-center">
              <motion.div
                animate={{
                  scale: current ? 1.08 : 1,
                  boxShadow: current
                    ? "0 0 0 1px rgba(34,211,238,.5), 0 0 32px rgba(34,211,238,.35)"
                    : "0 0 0 1px rgba(148,163,184,.14)",
                }}
                className={`relative z-10 grid h-14 w-14 shrink-0 place-items-center rounded-2xl transition-colors duration-500 ${
                  on ? "bg-raised text-cyan" : "bg-deep text-muted"
                }`}
              >
                <a.icon size={22} />
                {current && (
                  <span className="absolute -right-1 -top-1 flex h-3 w-3">
                    <span className="absolute h-full w-full animate-ping rounded-full bg-cyan opacity-70" />
                    <span className="relative h-3 w-3 rounded-full bg-cyan" />
                  </span>
                )}
              </motion.div>
              <div className="md:mt-4">
                <p className="font-mono text-[10px] uppercase tracking-widest text-muted">Agent 0{i + 1}</p>
                <p className={`font-display font-semibold transition-colors ${on ? "text-fg" : "text-muted"}`}>
                  {a.name}
                </p>
                <p className="mt-1 text-sm text-muted">{a.text}</p>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3 rounded-xl border border-dashed border-cyan/25 bg-cyan/[0.04] px-4 py-3 text-center text-sm">
        <ShieldCheck size={16} className="text-cyan" />
        <span className="text-fg/90">
          <strong className="font-semibold">Design principle:</strong> the LLM never calculates. Numbers come from
          deterministic code and trained models; the Checker confirms they weren’t changed.
        </span>
      </div>
    </div>
  );
}

export default function Overview() {
  const [stats, setStats] = useState<any>(null);
  useEffect(() => {
    getDashboard().then(setStats).catch(() => setStats(null));
  }, []);

  return (
    <div>
      {/* HERO */}
      <section className="grid items-center gap-10 pb-10 pt-4 lg:grid-cols-[1.05fr_1fr] lg:pt-10">
        <motion.div variants={stagger} initial="hidden" animate="show">
          <motion.div
            variants={fadeUp}
            className="inline-flex items-center gap-2 rounded-full border border-line bg-white/[0.03] py-1 pl-1 pr-3 text-xs text-muted"
          >
            <span className="rounded-full bg-cyan/15 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-cyan">
              Agentic AI
            </span>
            Evidence-grounded disruption detection
          </motion.div>
          <motion.h1
            variants={fadeUp}
            className="mt-6 font-display text-[2.6rem] font-semibold leading-[1.05] tracking-tight sm:text-6xl"
          >
            See supply chain disruption <span className="text-gradient">before it lands.</span>
          </motion.h1>
          <motion.p variants={fadeUp} className="mt-6 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
            SCOPE fuses machine learning, hybrid retrieval over contracts, and a team of verified agents — so every
            risk it reports comes with traceable evidence, not hallucinated numbers.
          </motion.p>

          <motion.div
            variants={fadeUp}
            className="mt-8 flex max-w-xl items-center gap-3 rounded-2xl border border-line bg-surface/80 p-2 pl-4 backdrop-blur"
          >
            <Sparkles size={16} className="shrink-0 text-cyan" />
            <div className="min-w-0 flex-1 truncate py-1.5">
              <Typewriter />
            </div>
            <Link to="/investigate" className="btn-primary shrink-0 px-4 py-2">
              Run <ArrowRight size={15} />
            </Link>
          </motion.div>

          <motion.div variants={fadeUp} className="mt-6 flex flex-wrap gap-3">
            <Link to="/dashboard" className="btn-ghost">
              Open dashboard
            </Link>
            <a href="#approach" className="btn-ghost">
              How it works
            </a>
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        >
          <NetworkHero />
        </motion.div>
      </section>

      {/* LIVE STRIP */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.6 }}
        className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-line bg-line md:grid-cols-4"
      >
        {[
          ["Orders analysed", stats?.total_orders, 0, ""],
          ["Vendors tracked", stats?.total_vendors, 0, ""],
          ["Late delivery rate", stats?.late_delivery_pct, 1, "%"],
          ["Unusual profiles", stats?.unusual_profile_count ?? stats?.anomaly_count, 0, ""],
        ].map(([label, v, d, s]) => (
          <div key={label as string} className="bg-surface/90 px-5 py-5 backdrop-blur">
            <p className="font-display text-2xl font-semibold sm:text-3xl">
              <CountUp value={v as number} decimals={d as number} suffix={s as string} />
            </p>
            <p className="mt-1 text-xs text-muted">{label as string}</p>
          </div>
        ))}
      </motion.div>
      {!stats && (
        <p className="mt-2 text-center font-mono text-[11px] text-muted">Live metrics appear when the API is running.</p>
      )}

      {/* PROBLEM */}
      <Section
        eyebrow="The problem"
        title="Signals are split across two worlds"
        text="Disruptions are caught late because the evidence lives in structured tables and unstructured documents — and analysts stitch them together by hand."
      >
        <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-stretch">
          {[
            {
              icon: Database,
              title: "Structured data",
              items: ["Orders & shipments", "Delivery dates", "Stock levels", "Supplier KPIs"],
              tone: "text-cyan bg-cyan/10",
            },
            null,
            {
              icon: FileText,
              title: "Unstructured text",
              items: ["Contract clauses", "SLA terms", "Penalty conditions", "Policies"],
              tone: "text-violet-soft bg-violet/10",
            },
          ].map((c, i) =>
            c ? (
              <motion.div
                key={c.title}
                initial={{ opacity: 0, x: i === 0 ? -24 : 24 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
                className="panel p-6"
              >
                <span className={`grid h-11 w-11 place-items-center rounded-xl ${c.tone}`}>
                  <c.icon size={20} />
                </span>
                <p className="mt-4 font-display text-lg font-semibold">{c.title}</p>
                <ul className="mt-3 grid grid-cols-2 gap-2 text-sm text-muted">
                  {c.items.map((x) => (
                    <li key={x} className="flex items-center gap-2">
                      <span className="h-1 w-1 rounded-full bg-muted" />
                      {x}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ) : (
              <motion.div
                key="join"
                initial={{ opacity: 0, scale: 0.6 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.3, type: "spring" }}
                className="flex items-center justify-center"
              >
                <div className="relative grid h-20 w-20 place-items-center rounded-full border border-cyan/30 bg-surface">
                  <span className="absolute inset-0 animate-pulse-ring rounded-full border border-cyan/40" />
                  <span className="font-display text-sm font-bold">SCOPE</span>
                </div>
              </motion.div>
            )
          )}
        </div>
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mx-auto mt-8 max-w-3xl text-center text-[15px] text-muted"
        >
          There is no open, low-cost system that detects disruption risk from both — and verifies each generated claim
          against its source before reporting it.
        </motion.p>
      </Section>

      {/* EXISTING */}
      <Section eyebrow="Landscape" title="Where existing tools fall short">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {comparisons.map((c, i) => (
            <motion.div
              key={c.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.5 }}
              className="panel"
            >
              <p className="font-display font-semibold">{c.name}</p>
              <p className="font-mono text-[11px] text-muted">{c.sub}</p>
              <p className="mt-4 border-t border-line pt-4 text-sm text-risk/90">{c.gap}</p>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* APPROACH */}
      <Section
        id="approach"
        eyebrow="Our approach"
        title="Three layers, one verified pipeline"
        text="Submit one goal. SCOPE plans, executes, explains and verifies the analysis end to end."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          {layers.map((l, i) => (
            <motion.div
              key={l.tag}
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              whileHover={{ y: -6 }}
              className="panel group overflow-hidden p-6"
            >
              <div
                className={`pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b ${l.color} to-transparent opacity-40 transition-opacity duration-500 group-hover:opacity-80`}
              />
              <div className="relative">
                <div className="flex items-center justify-between">
                  <span className={`font-mono text-xs uppercase tracking-widest ${l.accent}`}>{l.tag}</span>
                  <l.icon size={22} className={l.accent} />
                </div>
                <p className="mt-6 font-display text-2xl font-semibold">{l.title}</p>
                <ul className="mt-5 space-y-3">
                  {l.items.map((it) => (
                    <li key={it} className="flex gap-3 text-sm text-muted">
                      <CheckCircle2 size={16} className={`mt-0.5 shrink-0 ${l.accent}`} />
                      {it}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* AGENTS */}
      <Section eyebrow="Layer C in motion" title="A team of agents with a fact-checker">
        <AgentFlow />
      </Section>

      {/* EVALUATION */}
      <Section eyebrow="Evaluation" title="Measured, not assumed">
        <div className="grid gap-4 md:grid-cols-3">
          {[
            ["Machine learning", "Precision · Recall · F1 · PR-AUC for late delivery; MAE · RMSE for forecasting. Time-based split, no shuffling."],
            ["Retrieval", "Recall@k and Mean Reciprocal Rank on a hand-built question set."],
            ["End to end", "SCOPE vs. a plain LLM baseline on hallucination rate, unsupported-claim rate, detection rate and latency."],
          ].map(([t, d], i) => (
            <motion.div
              key={t}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="panel p-6"
            >
              <p className="font-mono text-xs text-cyan">0{i + 1}</p>
              <p className="mt-2 font-display text-lg font-semibold">{t}</p>
              <p className="mt-2 text-sm leading-relaxed text-muted">{d}</p>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* VALUE */}
      <Section eyebrow="Value" title="What SCOPE adds">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {values.map((v, i) => (
            <motion.div
              key={v.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: (i % 3) * 0.08 }}
              className="group flex gap-4 rounded-2xl border border-transparent p-5 transition hover:border-line hover:bg-surface/60"
            >
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/[0.04] text-cyan ring-1 ring-line transition group-hover:bg-cyan/10">
                <v.icon size={18} />
              </span>
              <div>
                <p className="font-semibold">{v.title}</p>
                <p className="mt-1 text-sm text-muted">{v.text}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* TEAM */}
      <Section eyebrow="Team" title="Built at UET Lahore" text="Institute of Data Sciences · Fifth semester · Session 2024–2028">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {team.map(([n, id], i) => (
            <motion.div
              key={id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="panel flex items-center gap-4"
            >
              <span className="grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-cyan/30 to-violet/30 font-display font-semibold">
                {n.split(" ").map((p) => p[0]).join("")}
              </span>
              <div>
                <p className="font-semibold">{n}</p>
                <p className="font-mono text-xs text-muted">{id}</p>
              </div>
            </motion.div>
          ))}
        </div>
        <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted">
          <Users size={15} className="text-cyan" /> Supervised by <span className="text-fg">Ms. Manal Iftikhar</span>
        </div>
      </Section>

      {/* CTA */}
      <motion.section
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-br from-cyan/15 via-surface to-violet/20 px-6 py-14 text-center sm:px-12"
      >
        <div className="bg-grid absolute inset-0 opacity-40" />
        <div className="relative">
          <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
            Ask a question. Get evidence.
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-muted">
            Launch an investigation and watch the agents plan, analyse, retrieve and verify in real time.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link to="/investigate" className="btn-primary">
              Start an investigation <ArrowRight size={16} />
            </Link>
            <Link to="/evidence" className="btn-ghost">
              Browse the evidence ledger
            </Link>
          </div>
        </div>
      </motion.section>
    </div>
  );
}
