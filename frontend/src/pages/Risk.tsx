import { useEffect, useState } from "react";
import { getDashboard, getShap } from "../api";

export default function Risk() {
  const [dash, setDash] = useState<any>(null);
  const [shap, setShap] = useState<any>(null);

  useEffect(() => {
    getDashboard().then(setDash);
    getShap()
      .then(setShap)
      .catch(() => setShap({ status: "unavailable" }));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Risk Analysis</h1>
      <div className="panel">
        <p>Late deliveries: {dash?.risk_distribution?.late ?? "—"}</p>
        <p>On-time: {dash?.risk_distribution?.on_time ?? "—"}</p>
        <p>Late %: {dash?.late_delivery_pct?.toFixed?.(2) ?? "—"}</p>
        <p>Unusual shipment profiles: {dash?.unusual_profile_count ?? dash?.anomaly_count ?? "—"}</p>
      </div>
      <div className="panel">
        <h2 className="font-display text-xl">SHAP / explainability</h2>
        <pre className="mt-3 overflow-auto text-xs">{JSON.stringify(shap, null, 2)}</pre>
      </div>
    </div>
  );
}
