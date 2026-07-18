import { FileText, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import type { Report } from "../types";

export default function Reports() {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const load = () => {
    api
      .getText("/reports/latest/markdown")
      .then(setMarkdown)
      .catch((e) => setError(e.message));
  };

  useEffect(load, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await api.post<Report>("/reports/generate", {});
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-white">Latest High-Risk Report</h1>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-2 rounded-lg bg-accent-600 px-4 py-2 text-sm font-medium text-white shadow-glow transition-opacity hover:bg-accent-500 disabled:opacity-50"
        >
          <RefreshCw size={14} className={generating ? "animate-spin" : ""} />
          {generating ? "Generating..." : "Generate now"}
        </button>
      </div>

      {error && <p className="text-red-400">{error}</p>}

      <div className="card p-6">
        {markdown ? (
          <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-400">{markdown}</pre>
        ) : (
          <EmptyState icon={FileText} message='No report yet — click "Generate now".' />
        )}
      </div>
    </div>
  );
}
