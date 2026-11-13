import { useState } from "react";
import { ragQuery } from "../api";

export default function Documents() {
  const [query, setQuery] = useState("vendor late delivery escalation policy");
  const [result, setResult] = useState<any>(null);

  async function ask() {
    setResult(await ragQuery(query));
  }

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Document Intelligence</h1>
      <p className="text-ink/70">
        Synthetic development documents are labeled and must not be treated as real contracts.
      </p>
      <div className="panel space-y-3">
        <textarea
          className="w-full rounded border border-ink/20 p-3"
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button onClick={ask} className="rounded bg-sea px-4 py-2 text-white">
          Retrieve grounded answer
        </button>
      </div>
      {result && (
        <div className="panel space-y-3">
          <pre className="whitespace-pre-wrap text-sm">{result.answer}</pre>
          <h3 className="font-semibold">Citations</h3>
          <ul className="list-disc pl-5 text-sm">
            {(result.citations || []).map((c: any, i: number) => (
              <li key={i}>
                {c.file_name} (page/chunk {c.page}) score={c.score?.toFixed?.(3)}{" "}
                {c.synthetic ? "[synthetic]" : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
