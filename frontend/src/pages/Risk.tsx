import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, BrainCircuit, CheckCircle2, Sigma } from "lucide-react";
import { getDashboard, getShap } from "../api";
import { Badge, EmptyState, PageHeader, Panel, Skeleton, StatCard } from "../components/ui";

const pretty = (f: string) => f.replace(/^(num|cat)__/, "").replace(/_/g, " ");

function Bars({
  items,
  valueKey,
  signed,
}: {
  items: any[];
  valueKey: string;
  signed?: boolean;
}) {
  const max = Math.max(0.0001, ...items.map((i) => Math.abs(i[valueKey])));
  return (
    <ul className="space-y-3">
      {items.map((it, i) => {
        const v = it[valueKey] as number;
        const w = (Math.abs(v) / max) * 100;
        const pos = v >= 0;
        return (
          <li key={it.feature} className="grid grid-cols-[minmax(0,11rem)_1fr_4.5rem] items-center gap-3 text-sm">
            <span className="truncate text-fg/90" title={it.feature}>
              {pretty(it.feature)}
            </span>
            <div className={`relative h-2 rounded-full bg-white/5 ${signed ? "" : ""}`}>
              {signed ? (
                <motion.div
                  className={`absolute top-0 h-full rounded-full ${pos ? "left-1/2 bg-risk" : "right-1/2 bg-cyan"}`}
                  initial={{ width: 0 }}
                  whileInView={{ width: `${w / 2}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.9, delay: i * 0.05, ease: [0.22, 1, 0.36, 1] }}
                />
              ) : (
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-cyan to-violet"
                  initial={{ width: 0 }}
                  whileInView={{ width: `${w}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.9, delay: i * 0.05, ease: [0.22, 1, 0.36, 1] }}
                />
              )}
              {signed && <span className="absolute left-1/2 top-[-3px] h-[14px] w-px bg-line" />}
            </div>
            <span className="text-right font-mono text-xs tabular-nums text-muted">
              {signed && pos ? "+" : ""}
              {v.toFixed(3)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export default function Risk() {
  const [dash, setDash] = useState<any>(null);
  const [shap, setShap] = useState<any>(null);

  useEffect(() => {
    getDashboard().then(setDash).catch(() => setDash({}));
    getShap()
      .then(setShap)
      .catch(() => setShap({ status: "unavailable" }));
  }, []);

  const global: any[] = shap?.top_global || [];
  const local: any[] = shap?.local_example?.top_features || [];

  return (
    <>
      <PageHeader
        eyebrow="Explainability"
        title="Risk Analysis"
        description="Which features drive late-delivery predictions — globally across the fleet, and for an individual shipment."
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard index={0} label="Late deliveries" value={dash?.risk_distribution?.late} icon={<AlertTriangle size={17} />} tone="risk" />
        <StatCard index={1} label="On-time deliveries" value={dash?.risk_distribution?.on_time} icon={<CheckCircle2 size={17} />} tone="ok" />
        <StatCard index={2} label="Late rate" value={dash?.late_delivery_pct} decimals={2} suffix="%" icon={<Sigma size={17} />} tone="warn" />
        <StatCard
          index={3}
          label="Unusual profiles"
          value={dash?.unusual_profile_count ?? dash?.anomaly_count}
          icon={<BrainCircuit size={17} />}
          tone="violet"
        />
      </div>

      {shap === null ? (
        <Skeleton className="mt-4 h-80" />
      ) : shap.status !== "ok" ? (
        <Panel className="mt-4">
          <EmptyState
            icon={<BrainCircuit size={22} />}
            title="SHAP report unavailable"
            text="Run the explainability phase in the backend to generate feature attributions."
          />
        </Panel>
      ) : (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <Panel delay={0.1}>
            <div className="mb-5 flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="panel-title">Global feature importance</p>
                <p className="text-sm text-muted">Mean |SHAP| over {shap.n_samples} samples</p>
              </div>
              <div className="flex gap-2">
                <Badge tone="cyan">{shap.model_name}</Badge>
                <Badge>{shap.explainer}</Badge>
              </div>
            </div>
            <Bars items={global} valueKey="mean_abs_shap" />
          </Panel>
          <Panel delay={0.2}>
            <div className="mb-5">
              <p className="panel-title">Local explanation</p>
              <p className="text-sm text-muted">
                Shipment <span className="font-mono text-cyan">#{shap.local_example?.row_id}</span> —{" "}
                <span className="text-risk">red</span> pushes toward late, <span className="text-cyan">cyan</span> toward
                on-time
              </p>
            </div>
            <Bars items={local} valueKey="shap" signed />
          </Panel>
        </div>
      )}
    </>
  );
}
