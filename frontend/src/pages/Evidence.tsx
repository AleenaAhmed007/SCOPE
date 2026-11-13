import { useEffect, useState } from "react";
import { getEvidence } from "../api";

export default function Evidence() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    getEvidence().then((d) => setItems(d.items || []));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Evidence Explorer</h1>
      <div className="panel overflow-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-ink/60">
              <th className="p-2">ID</th>
              <th className="p-2">Type</th>
              <th className="p-2">Source</th>
              <th className="p-2">Order</th>
              <th className="p-2">Status</th>
              <th className="p-2">Claim</th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => (
              <tr key={e.evidence_id} className="border-t border-ink/5 align-top">
                <td className="p-2 font-mono text-xs">{e.evidence_id.slice(0, 8)}</td>
                <td className="p-2">{e.evidence_type}</td>
                <td className="p-2">{e.source}</td>
                <td className="p-2">{e.related_order_id}</td>
                <td className="p-2">{e.validation_status}</td>
                <td className="p-2">{e.claim}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
