import { useEffect, useState } from "react";
import { getVendorSegments, getVendors } from "../api";
import { Scatter, ScatterChart, Tooltip, XAxis, YAxis, ResponsiveContainer, ZAxis } from "recharts";

export default function Vendors() {
  const [vendors, setVendors] = useState<any[]>([]);
  const [segments, setSegments] = useState<any[]>([]);

  useEffect(() => {
    getVendors().then((d) => setVendors(d.items || []));
    getVendorSegments()
      .then((d) => setSegments(d.items || []))
      .catch(() => setSegments([]));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Vendor Intelligence</h1>
      <div className="panel h-96">
        <h2 className="mb-3 font-display text-xl">Late rate vs shipment volume</h2>
        <ResponsiveContainer width="100%" height="85%">
          <ScatterChart>
            <XAxis dataKey="shipment_count" name="Shipments" />
            <YAxis dataKey="late_rate" name="Late rate" />
            <ZAxis range={[60, 60]} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={vendors.filter((v) => v.late_rate != null)} fill="#1B6B93" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="panel overflow-auto">
        <h2 className="mb-3 font-display text-xl">Segments</h2>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-ink/60">
              <th className="p-2">Vendor</th>
              <th className="p-2">Segment</th>
              <th className="p-2">Shipments</th>
              <th className="p-2">Late rate</th>
            </tr>
          </thead>
          <tbody>
            {(segments.length ? segments : vendors).slice(0, 40).map((v: any) => (
              <tr key={v.Vendor} className="border-t border-ink/5">
                <td className="p-2">{v.Vendor}</td>
                <td className="p-2">{v.segment ?? "—"}</td>
                <td className="p-2">{v.shipment_count}</td>
                <td className="p-2">
                  {v.late_rate != null ? (v.late_rate * 100).toFixed(1) + "%" : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
