import { useEffect, useState } from "react";
import { getAnomaly, getOrder, getOrders, predictDuration, predictInventoryStockout, predictLate } from "../api";

export default function Orders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [orderId, setOrderId] = useState(1);
  const [detail, setDetail] = useState<any>(null);
  const [pred, setPred] = useState<any>(null);

  useEffect(() => {
    getOrders(30).then((d) => setOrders(d.items || []));
  }, []);

  async function investigate() {
    const [order, late, duration, anomaly, inventory] = await Promise.all([
      getOrder(orderId),
      predictLate(orderId),
      predictDuration(orderId),
      getAnomaly(orderId).catch(() => null),
      predictInventoryStockout(orderId),
    ]);
    setDetail(order);
    setPred({ late, duration, anomaly, inventory });
  }

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Order Investigation</h1>
      <div className="panel flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Order ID
          <input
            className="mt-1 block rounded border border-ink/20 px-3 py-2"
            type="number"
            value={orderId}
            onChange={(e) => setOrderId(Number(e.target.value))}
          />
        </label>
        <button
          onClick={investigate}
          className="rounded bg-sea px-4 py-2 text-white hover:bg-sea/90"
        >
          Run prediction suite
        </button>
      </div>
      {pred && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="panel">
            <h3 className="font-semibold">Late delivery</h3>
            <p>Prob: {(pred.late.late_probability * 100).toFixed(1)}%</p>
            <p>Pred: {pred.late.late_prediction ? "Late" : "On-time"}</p>
          </div>
          <div className="panel">
            <h3 className="font-semibold">Duration</h3>
            <p>{pred.duration.predicted_duration_days.toFixed(1)} days</p>
            {pred.duration.low_confidence && (
              <p className="text-sm text-amber-700">Low confidence: validation did not beat the median baseline.</p>
            )}
          </div>
          <div className="panel">
            <h3 className="font-semibold">Inventory stockout (experimental)</h3>
            <p>Risk: {(pred.inventory.stockout_probability * 100).toFixed(1)}%</p>
            <p>Pred: {pred.inventory.stockout_prediction ? "Stockout" : "No stockout"}</p>
            {pred.inventory.low_confidence && (
              <p className="text-sm text-amber-700">Low confidence: model did not beat the prevalence baseline.</p>
            )}
          </div>
          <div className="panel">
            <h3 className="font-semibold">Unusual shipment profile</h3>
            <p>{pred.anomaly ? `score ${pred.anomaly.anomaly_score?.toFixed?.(3)}` : "n/a"}</p>
          </div>
        </div>
      )}
      {detail && (
        <pre className="panel overflow-auto text-xs">{JSON.stringify(detail, null, 2)}</pre>
      )}
      <div className="panel overflow-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-ink/60">
              <th className="p-2">ID</th>
              <th className="p-2">Vendor</th>
              <th className="p-2">Country</th>
              <th className="p-2">Mode</th>
              <th className="p-2">Late</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.ID} className="border-t border-ink/5">
                <td className="p-2">{o.ID}</td>
                <td className="p-2">{o.Vendor}</td>
                <td className="p-2">{o.Country}</td>
                <td className="p-2">{o.Shipment_Mode}</td>
                <td className="p-2">{o.is_late}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
