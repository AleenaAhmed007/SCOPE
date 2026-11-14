import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Activity, AlertTriangle, ArrowRight, Clock, FileSearch, Package, Truck } from "lucide-react";
import { getDashboard } from "../api";
import { ErrorState, PageHeader, Panel, Skeleton, StatCard, chartTheme } from "../components/ui";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => setError(e.message || "Failed to load dashboard"));
  }, []);

  const header = (
    <PageHeader
      eyebrow="Operations"
      title="Operations Dashboard"
      description="A live view of shipment volume, vendor coverage and delivery risk across the network."
      actions={
        <Link to="/investigate" className="btn-primary">
          New investigation <ArrowRight size={15} />
        </Link>
      }
    />
  );

  if (error)
    return (
      <>
        {header}
        <ErrorState message={error} />
      </>
    );

  if (!data)
    return (
      <>
        {header}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="mt-4 h-80" />
      </>
    );

  const onTime = data.risk_distribution?.on_time ?? 0;
  const late = data.risk_distribution?.late ?? 0;
  const total = onTime + late || 1;
  const pie = [
    { name: "On-time", value: onTime, color: "#22D3EE" },
    { name: "Late", value: late, color: "#F87171" },
  ];
  const recent: any[] = data.recent_investigations || [];

  return (
    <>
      {header}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard index={0} label="Total orders" value={data.total_orders} icon={<Package size={17} />} />
        <StatCard index={1} label="Vendors" value={data.total_vendors} icon={<Truck size={17} />} tone="violet" />
        <StatCard
          index={2}
          label="Late delivery rate"
          value={data.late_delivery_pct}
          decimals={2}
          suffix="%"
          icon={<AlertTriangle size={17} />}
          tone="risk"
        />
        <StatCard
          index={3}
          label="Avg delivery duration"
          value={data.avg_delivery_duration}
          decimals={1}
          suffix=" d"
          icon={<Clock size={17} />}
          tone="warn"
        />
        <StatCard
          index={4}
          label="Unusual shipment profiles"
          value={data.unusual_profile_count ?? data.anomaly_count}
          icon={<Activity size={17} />}
          tone="violet"
        />
        <StatCard
          index={5}
          label="Recent investigations"
          value={recent.length}
          icon={<FileSearch size={17} />}
          tone="ok"
        />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <Panel delay={0.15}>
          <p className="panel-title">Risk distribution</p>
          <p className="text-sm text-muted">Historical on-time vs. late deliveries</p>
          <div className="mt-2 grid items-center gap-4 sm:grid-cols-[1fr_auto]">
            <div className="relative h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pie}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="64%"
                    outerRadius="88%"
                    paddingAngle={3}
                    stroke="none"
                    animationDuration={1200}
                  >
                    {pie.map((p) => (
                      <Cell key={p.name} fill={p.color} />
                    ))}
                  </Pie>
                  <Tooltip {...chartTheme.tooltip} />
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
                <div>
                  <p className="font-display text-3xl font-semibold">{((late / total) * 100).toFixed(1)}%</p>
                  <p className="text-xs text-muted">late</p>
                </div>
              </div>
            </div>
            <div className="space-y-4 sm:pr-4">
              {pie.map((p) => (
                <div key={p.name}>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: p.color }} />
                    {p.name}
                  </div>
                  <p className="mt-1 font-display text-xl font-semibold tabular-nums">{p.value.toLocaleString()}</p>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        <Panel delay={0.25}>
          <p className="panel-title">Delivery health</p>
          <p className="text-sm text-muted">Share of orders by outcome</p>
          <div className="mt-6 space-y-6">
            {pie.map((p, i) => (
              <div key={p.name}>
                <div className="mb-2 flex justify-between text-sm">
                  <span>{p.name}</span>
                  <span className="font-mono text-muted">{((p.value / total) * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-white/5">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: p.color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(p.value / total) * 100}%` }}
                    transition={{ duration: 1.2, delay: 0.3 + i * 0.15, ease: [0.22, 1, 0.36, 1] }}
                  />
                </div>
              </div>
            ))}
          </div>

          <p className="mt-8 panel-title">Recent investigations</p>
          {recent.length === 0 ? (
            <p className="mt-2 text-sm text-muted">No investigations yet.</p>
          ) : (
            <ul className="mt-3 divide-y divide-line">
              {recent.slice(0, 4).map((r: any, i: number) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + i * 0.06 }}
                  className="flex items-center justify-between gap-3 py-2.5 text-sm"
                >
                  <span className="truncate">{r.query ?? r.title ?? r.investigation_id ?? `Investigation ${i + 1}`}</span>
                  <span className="shrink-0 font-mono text-xs text-muted">
                    {r.order_id != null ? `#${r.order_id}` : r.status ?? ""}
                  </span>
                </motion.li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </>
  );
}
