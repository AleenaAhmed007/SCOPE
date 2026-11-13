import { useState } from "react";
import { runInvestigation } from "../api";

export default function Investigate() {
  const [orderId, setOrderId] = useState(1);
  const [query, setQuery] = useState("Investigate potential disruption and late delivery risk");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    try {
      setResult(await runInvestigation(query, orderId));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Agentic Investigation</h1>
      <div className="panel grid gap-3 md:grid-cols-[1fr_auto_auto]">
        <input
          className="rounded border border-ink/20 px-3 py-2"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <input
          className="rounded border border-ink/20 px-3 py-2"
          type="number"
          value={orderId}
          onChange={(e) => setOrderId(Number(e.target.value))}
        />
        <button
          onClick={run}
          disabled={loading}
          className="rounded bg-ember px-4 py-2 text-white disabled:opacity-60"
        >
          {loading ? "Running…" : "Start investigation"}
        </button>
      </div>
      {result && (
        <div className="space-y-4">
          <div className="panel">
            <h2 className="font-display text-xl">Plan</h2>
            <ol className="mt-2 list-decimal pl-5 text-sm">
              {(result.plan || []).map((p: string) => (
                <li key={p}>{p}</li>
              ))}
            </ol>
            <p className="mt-3 text-sm">Status: {result.status}</p>
          </div>
          <div className="panel">
            <h2 className="font-display text-xl">ML findings</h2>
            <pre className="overflow-auto text-xs">{JSON.stringify(result.ml_findings, null, 2)}</pre>
          </div>
          <div className="panel">
            <h2 className="font-display text-xl">Document findings</h2>
            <pre className="whitespace-pre-wrap text-sm">{result.document_findings?.answer}</pre>
          </div>
          <div className="panel">
            <h2 className="font-display text-xl">Checker</h2>
            <pre className="overflow-auto text-xs">{JSON.stringify(result.checker_result, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
