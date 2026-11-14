import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { getVendorSegments, getVendors } from "../api";
import { Badge, ErrorState, PageHeader, Panel, Skeleton, chartTheme } from "../components/ui";

const segmentTones = ["cyan", "violet", "ok", "warn", "risk"] as const;

export default function Vendors() {
  const [vendors, setVendors] = useState<any[] | null>(null);
  const [segments, setSegments] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getVendors()
      .then((d) => setVendors(d.items || []))
      .catch((e) => {
        setVendors([]);
        setError(e.message || "Failed to load vendors");
      });
    getVendorSegments()
      .then((d) => setSegments(d.items || []))
      .catch(() => setSegments([]));
  }, []);

  const segIndex = useMemo(() => {
    const keys = Array.from(new Set(segments.map((s) => String(s.segment))));
    return (s: any) => keys.indexOf(String(s));
  }, [segments]);

  const rows = (segments.length ? segments : vendors || []).slice(0, 40);
  const maxLate = Math.max(0.0001, ...rows.map((r: any) => r.late_rate ?? 0));

  return (
    <>
      <PageHeader
        eyebrow="Supplier intelligence"
        title="Vendor Intelligence"
        description="Compare vendors by shipment volume and late-delivery rate, segmented with K-Means on performance features."
      />
      {error && <ErrorState message={error} />}

      <Panel className="h-[420px]">
        <p className="panel-title">Late rate vs. shipment volume</p>
        <p className="text-sm text-muted">Each point is a vendor</p>
        {vendors === null ? (
          <Skeleton className="mt-4 h-[320px]" />
        ) : (
          <ResponsiveContainer width="100%" height="85%">
            <ScatterChart margin={{ top: 20, right: 10, bottom: 10, left: -10 }}>
              <CartesianGrid stroke={chartTheme.grid} />
              <XAxis
                dataKey="shipment_count"
                name="Shipments"
                stroke={chartTheme.axis}
                tick={{ fontSize: 11 }}
                type="number"
                scale="log"
                domain={["auto", "auto"]}
                allowDataOverflow
              />
              <YAxis
                dataKey="late_rate"
                name="Late rate"
                stroke={chartTheme.axis}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${Math.round(v * 100)}%`}
              />
              <ZAxis range={[50, 50]} />
              <Tooltip
                {...chartTheme.tooltip}
                cursor={{ strokeDasharray: "3 3", stroke: "#22D3EE" }}
                formatter={(v: any, n: any) => (n === "Late rate" ? `${(v * 100).toFixed(1)}%` : v)}
              />
              <Scatter
                data={vendors.filter((v) => v.late_rate != null && v.shipment_count > 0)}
                fill="#22D3EE"
                fillOpacity={0.75}
                animationDuration={1200}
              />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </Panel>

      <Panel className="mt-4 overflow-hidden p-0" delay={0.1}>
        <div className="border-b border-line p-5">
          <p className="panel-title">Segments</p>
          <p className="text-sm text-muted">Top {rows.length} vendors</p>
        </div>
        <div className="max-h-[520px] overflow-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Segment</th>
                <th className="text-right">Shipments</th>
                <th className="w-1/3">Late rate</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((v: any, i: number) => (
                <motion.tr
                  key={v.Vendor}
                  initial={{ opacity: 0, y: 6 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: Math.min(i * 0.015, 0.3) }}
                >
                  <td className="max-w-xs truncate">{v.Vendor}</td>
                  <td>
                    {v.segment != null ? (
                      <Badge tone={segmentTones[Math.max(0, segIndex(v.segment)) % segmentTones.length]}>
                        {v.segment}
                      </Badge>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td className="text-right font-mono tabular-nums">{v.shipment_count}</td>
                  <td>
                    {v.late_rate != null ? (
                      <div className="flex items-center gap-3">
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
                          <motion.div
                            className="h-full rounded-full bg-gradient-to-r from-warn to-risk"
                            initial={{ width: 0 }}
                            whileInView={{ width: `${(v.late_rate / maxLate) * 100}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.9, ease: "easeOut" }}
                          />
                        </div>
                        <span className="w-12 text-right font-mono text-xs tabular-nums">
                          {(v.late_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
