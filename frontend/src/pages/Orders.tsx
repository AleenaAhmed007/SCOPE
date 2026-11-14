import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, ChevronDown, Clock, Play, Search, TriangleAlert } from "lucide-react";
import { getAnomaly, getOrder, getOrders, predictDuration, predictLate } from "../api";
import { Badge, ErrorState, PageHeader, Panel, Skeleton, Spinner } from "../components/ui";

function Gauge({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(1, value));
  const r = 52;
  const c = Math.PI * r;
  const color = pct >= 0.5 ? "#F87171" : pct >= 0.25 ? "#FBBF24" : "#34D399";
  return (
    <svg viewBox="0 0 128 72" className="w-40">
      <path d="M12 66 A52 52 0 0 1 116 66" fill="none" stroke="rgba(148,163,184,.12)" strokeWidth="10" strokeLinecap="round" />
      <motion.path
        d="M12 66 A52 52 0 0 1 116 66"
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={c}
        initial={{ strokeDashoffset: c }}
        animate={{ strokeDashoffset: c * (1 - pct) }}
        transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
      />
    </svg>
  );
}

export default function Orders() {
  const [orders, setOrders] = useState<any[] | null>(null);
  const [orderId, setOrderId] = useState(1);
  const [detail, setDetail] = useState<any>(null);
  const [pred, setPred] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showRaw, setShowRaw] = useState(false);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    getOrders(30)
      .then((d) => setOrders(d.items || []))
      .catch((e) => {
        setOrders([]);
        setError(e.message || "Failed to load orders");
      });
  }, []);

  async function investigate(id = orderId) {
    setLoading(true);
    setError("");
    try {
      const [order, late, duration, anomaly] = await Promise.all([
        getOrder(id),
        predictLate(id),
        predictDuration(id),
        getAnomaly(id).catch(() => null),
      ]);
      setDetail(order);
      setPred({ late, duration, anomaly });
    } catch (e: any) {
      setError(e.message || "Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  const rows = (orders || []).filter((o) =>
    !filter ? true : `${o.ID} ${o.Vendor} ${o.Country} ${o.Shipment_Mode}`.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <>
      <PageHeader
        eyebrow="Layer A · Machine learning"
        title="Order Investigation"
        description="Run the full prediction suite — late-delivery probability, duration estimate and unusual-profile score — for any order."
      />

      <Panel className="flex flex-wrap items-end gap-3">
        <label className="flex-1 text-sm text-muted sm:max-w-xs">
          Order ID
          <input
            className="field mt-1.5 font-mono"
            type="number"
            value={orderId}
            onChange={(e) => setOrderId(Number(e.target.value))}
            onKeyDown={(e) => e.key === "Enter" && investigate()}
          />
        </label>
        <button onClick={() => investigate()} disabled={loading} className="btn-primary">
          {loading ? <Spinner label="Running models…" /> : (<><Play size={15} /> Run prediction suite</>)}
        </button>
      </Panel>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}

      <AnimatePresence mode="wait">
        {pred && (
          <motion.div
            key={detail?.ID ?? orderId}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 grid gap-4 md:grid-cols-3"
          >
            <div className="panel flex flex-col items-center text-center">
              <div className="flex w-full items-center justify-between">
                <p className="panel-title">Late delivery</p>
                <TriangleAlert size={16} className="text-muted" />
              </div>
              <div className="relative mt-4">
                <Gauge value={pred.late.late_probability} />
                <p className="absolute inset-x-0 bottom-0 font-display text-2xl font-semibold">
                  {(pred.late.late_probability * 100).toFixed(1)}%
                </p>
              </div>
              <div className="mt-3">
                {pred.late.late_prediction ? <Badge tone="risk">Predicted late</Badge> : <Badge tone="ok">Predicted on-time</Badge>}
              </div>
            </div>
            <div className="panel">
              <div className="flex items-center justify-between">
                <p className="panel-title">Delivery duration</p>
                <Clock size={16} className="text-muted" />
              </div>
              <p className="mt-6 font-display text-5xl font-semibold tracking-tight">
                {pred.duration.predicted_duration_days.toFixed(1)}
                <span className="ml-1 text-lg text-muted">days</span>
              </p>
              {pred.duration.low_confidence ? (
                <p className="mt-4 rounded-lg bg-warn/10 px-3 py-2 text-xs text-warn">
                  Low confidence: validation did not beat the median baseline.
                </p>
              ) : (
                <p className="mt-4 text-xs text-muted">Model estimate</p>
              )}
            </div>
            <div className="panel">
              <div className="flex items-center justify-between">
                <p className="panel-title">Unusual shipment profile</p>
                <Activity size={16} className="text-muted" />
              </div>
              {pred.anomaly ? (
                <>
                  <p className="mt-6 font-display text-5xl font-semibold tracking-tight">
                    {pred.anomaly.anomaly_score?.toFixed?.(3)}
                  </p>
                  <div className="mt-4">
                    {pred.anomaly.is_anomaly ? <Badge tone="warn">Flagged as unusual</Badge> : <Badge tone="ok">Typical profile</Badge>}
                  </div>
                </>
              ) : (
                <p className="mt-6 text-muted">n/a</p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {detail && (
        <div className="mt-4">
          <button onClick={() => setShowRaw((s) => !s)} className="flex items-center gap-2 text-sm text-muted hover:text-fg">
            <motion.span animate={{ rotate: showRaw ? 180 : 0 }}>
              <ChevronDown size={16} />
            </motion.span>
            Raw order record
          </button>
          <AnimatePresence>
            {showRaw && (
              <motion.pre
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="panel mt-2 max-h-96 overflow-auto font-mono text-xs text-muted"
              >
                {JSON.stringify(detail, null, 2)}
              </motion.pre>
            )}
          </AnimatePresence>
        </div>
      )}

      <Panel className="mt-6 overflow-hidden p-0" delay={0.1}>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line p-5">
          <div>
            <p className="panel-title">Recent orders</p>
            <p className="text-sm text-muted">Click a row to run its predictions</p>
          </div>
          <div className="relative w-full sm:w-64">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input className="field pl-9" placeholder="Filter…" value={filter} onChange={(e) => setFilter(e.target.value)} />
          </div>
        </div>
        <div className="max-h-[480px] overflow-auto">
          {orders === null ? (
            <div className="space-y-2 p-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : (
            <table className="table-base">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Vendor</th>
                  <th>Country</th>
                  <th>Mode</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((o, i) => (
                  <motion.tr
                    key={o.ID}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: Math.min(i * 0.02, 0.4) }}
                    onClick={() => {
                      setOrderId(o.ID);
                      investigate(o.ID);
                    }}
                    className="cursor-pointer"
                  >
                    <td className="font-mono text-cyan">{o.ID}</td>
                    <td>{o.Vendor}</td>
                    <td className="text-muted">{o.Country}</td>
                    <td className="text-muted">{o.Shipment_Mode}</td>
                    <td>
                      {o.is_late == null ? (
                        <Badge>unknown</Badge>
                      ) : Number(o.is_late) ? (
                        <Badge tone="risk">Late</Badge>
                      ) : (
                        <Badge tone="ok">On-time</Badge>
                      )}
                    </td>
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
