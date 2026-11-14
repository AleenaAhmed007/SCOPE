import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CircleAlert, CircleCheck, Clock, Search, ShieldCheck } from "lucide-react";
import { getEvidence } from "../api";
import { Badge, EmptyState, ErrorState, PageHeader, Panel, Skeleton, StatCard } from "../components/ui";

function statusTone(s: string) {
  if (s === "validated" || s === "supported") return "ok" as const;
  if (s === "needs_review" || s === "unsupported") return "warn" as const;
  if (s === "corrected") return "cyan" as const;
  return "neutral" as const;
}

export default function Evidence() {
  const [items, setItems] = useState<any[] | null>(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");

  useEffect(() => {
    getEvidence()
      .then((d) => setItems(d.items || []))
      .catch((e) => {
        setItems([]);
        setError(e.message || "Failed to load evidence");
      });
  }, []);

  const statuses = useMemo(
    () => Array.from(new Set((items || []).map((e) => e.validation_status).filter(Boolean))),
    [items]
  );
  const count = (s: string) => (items || []).filter((e) => e.validation_status === s).length;
  const rows = (items || []).filter(
    (e) =>
      (filter === "all" || e.validation_status === filter) &&
      (!q || `${e.claim} ${e.source} ${e.evidence_type}`.toLowerCase().includes(q.toLowerCase()))
  );

  return (
    <>
      <PageHeader
        eyebrow="Evidence ledger"
        title="Evidence Explorer"
        description="Every finding SCOPE reports is written here first — and checked against its source before it reaches a report."
      />
      {error && <ErrorState message={error} />}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard index={0} label="Total evidence" value={items?.length} icon={<ShieldCheck size={17} />} />
        <StatCard index={1} label="Validated" value={items ? count("validated") : null} icon={<CircleCheck size={17} />} tone="ok" />
        <StatCard
          index={2}
          label="Needs review"
          value={items ? count("needs_review") : null}
          icon={<CircleAlert size={17} />}
          tone="warn"
        />
      </div>

      <Panel className="mt-4 overflow-hidden p-0" delay={0.1}>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line p-4">
          <div className="flex flex-wrap gap-1 rounded-full border border-line bg-deep/60 p-1">
            {["all", ...statuses].map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`relative rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  filter === s ? "text-void" : "text-muted hover:text-fg"
                }`}
              >
                {filter === s && (
                  <motion.span layoutId="ev-filter" className="absolute inset-0 rounded-full bg-cyan" transition={{ type: "spring", stiffness: 400, damping: 32 }} />
                )}
                <span className="relative">{s.replace("_", " ")}</span>
              </button>
            ))}
          </div>
          <div className="relative w-full sm:w-72">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input className="field pl-9" placeholder="Search claims…" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
        </div>

        <div className="max-h-[620px] overflow-auto">
          {items === null ? (
            <div className="space-y-2 p-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : rows.length === 0 ? (
            <EmptyState icon={<Clock size={22} />} title="No evidence yet" text="Run an investigation to populate the ledger." />
          ) : (
            <table className="table-base">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Source</th>
                  <th>Order</th>
                  <th>Status</th>
                  <th>Claim</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((e, i) => (
                  <motion.tr
                    key={e.evidence_id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(i * 0.02, 0.4) }}
                    className="align-top"
                  >
                    <td className="font-mono text-xs text-cyan">{String(e.evidence_id).slice(0, 8)}</td>
                    <td>
                      <Badge tone={e.evidence_type === "document" ? "violet" : "cyan"}>{e.evidence_type}</Badge>
                    </td>
                    <td className="text-muted">{e.source}</td>
                    <td className="font-mono text-xs">{e.related_order_id ?? "—"}</td>
                    <td>
                      <Badge tone={statusTone(e.validation_status)}>{String(e.validation_status).replace("_", " ")}</Badge>
                    </td>
                    <td className="min-w-[18rem] text-fg/85">{e.claim}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Panel>
    </>
  );
}
