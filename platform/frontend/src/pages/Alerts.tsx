import { ChevronLeft, ChevronRight, Inbox } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { RiskScoreBar } from "../components/RiskScoreBar";
import { TierBadge } from "../components/TierBadge";
import type { AlertPage } from "../types";

const TIERS = ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"];
const PAGE_SIZE = 10;

export default function Alerts() {
  const [page, setPage] = useState<AlertPage | null>(null);
  const [tier, setTier] = useState("ALL");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
    if (tier !== "ALL") params.set("tier", tier);

    api
      .get<AlertPage>(`/alerts?${params.toString()}`)
      .then(setPage)
      .catch((e) => setError(e.message));
  }, [tier, offset]);

  const handleTierChange = (t: string) => {
    setTier(t);
    setOffset(0);
  };

  const total = page?.total ?? 0;
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + PAGE_SIZE, total);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          {TIERS.map((t) => (
            <button
              key={t}
              onClick={() => handleTierChange(t)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                tier === t
                  ? "bg-accent-600/20 text-accent-400 ring-1 ring-inset ring-accent-600/30"
                  : "bg-white/[0.03] text-slate-400 ring-1 ring-inset ring-white/[0.06] hover:text-slate-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-500">
          {total > 0 ? `Showing ${from}–${to} of ${total}` : "No results"}
        </p>
      </div>

      {error && <p className="text-red-400">Failed to load alerts: {error}</p>}

      <div className="card overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-white/[0.02] text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">ID</th>
              <th className="px-4 py-3 font-medium">Amount</th>
              <th className="px-4 py-3 font-medium">Tier</th>
              <th className="px-4 py-3 font-medium">Risk Score</th>
            </tr>
          </thead>
          <tbody>
            {page?.items.map((alert) => (
              <tr key={alert.id} className="border-t border-white/[0.04] hover:bg-white/[0.02]">
                <td className="px-4 py-3">
                  <Link to={`/alerts/${alert.id}`} className="text-accent-400 hover:underline">
                    {alert.id}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-300">${alert.amount.toFixed(2)}</td>
                <td className="px-4 py-3">
                  <TierBadge tier={alert.risk_tier} />
                </td>
                <td className="px-4 py-3">
                  <RiskScoreBar score={alert.risk_score} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {page && page.items.length === 0 && !error && (
          <EmptyState icon={Inbox} message="No alerts match this filter." />
        )}
      </div>

      {total > PAGE_SIZE && (
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
            className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs text-slate-400 ring-1 ring-inset ring-white/[0.06] hover:text-slate-200 disabled:opacity-30"
          >
            <ChevronLeft size={14} /> Prev
          </button>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={to >= total}
            className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs text-slate-400 ring-1 ring-inset ring-white/[0.06] hover:text-slate-200 disabled:opacity-30"
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
