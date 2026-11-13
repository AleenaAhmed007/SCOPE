import { useEffect, useState } from "react";
import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { getDashboard } from "../api";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => setError(e.message || "Failed to load dashboard"));
  }, []);

  if (error) return <p className="text-ember">API error: {error}. Is FastAPI running on :8000?</p>;
  if (!data) return <p>Loading dashboard…</p>;

  const pie = [
    { name: "On-time", value: data.risk_distribution.on_time },
    { name: "Late", value: data.risk_distribution.late },
  ];

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Operations Dashboard</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[
          ["Total orders", data.total_orders],
          ["Vendors", data.total_vendors],
          ["Late %", data.late_delivery_pct?.toFixed?.(2)],
          ["Avg duration (days)", data.avg_delivery_duration?.toFixed?.(1)],
          ["Unusual shipment profiles", data.unusual_profile_count ?? data.anomaly_count],
          ["Recent investigations", data.recent_investigations?.length ?? 0],
        ].map(([label, value]) => (
          <div key={String(label)} className="panel">
            <p className="text-sm text-ink/60">{label}</p>
            <p className="mt-2 font-display text-3xl">{value ?? "—"}</p>
          </div>
        ))}
      </div>
      <div className="panel h-80">
        <h2 className="mb-4 font-display text-xl">Risk distribution</h2>
        <ResponsiveContainer width="100%" height="85%">
          <PieChart>
            <Pie data={pie} dataKey="value" nameKey="name" outerRadius={100} label>
              <Cell fill="#1B6B93" />
              <Cell fill="#C45C26" />
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
