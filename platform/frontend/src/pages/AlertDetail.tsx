import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { RiskScoreBar } from "../components/RiskScoreBar";
import { ShapBarChart } from "../components/ShapBarChart";
import { SignalBreakdown } from "../components/SignalBreakdown";
import { TierBadge } from "../components/TierBadge";
import type { AlertDetail as AlertDetailType } from "../types";

export default function AlertDetail() {
  const { id } = useParams<{ id: string }>();
  const [alert, setAlert] = useState<AlertDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .get<AlertDetailType>(`/alerts/${id}`)
      .then(setAlert)
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return <p className="text-red-400">Failed to load alert: {error}</p>;
  if (!alert) return <p className="text-slate-500">Loading...</p>;

  return (
    <div className="space-y-6">
      <Link to="/alerts" className="flex w-fit items-center gap-1 text-sm text-accent-400 hover:underline">
        <ArrowLeft size={14} /> Back to alerts
      </Link>

      <div className="card p-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white">{alert.id}</h1>
          <TierBadge tier={alert.risk_tier} />
        </div>
        <p className="mt-1 text-sm text-slate-500">{new Date(alert.timestamp).toLocaleString()}</p>

        <div className="mt-5 grid grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-slate-500">Amount</p>
            <p className="font-medium text-slate-200">${alert.amount.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-slate-500">Risk Score</p>
            <RiskScoreBar score={alert.risk_score} />
          </div>
          <div>
            <p className="text-slate-500">DBSCAN / Classifier</p>
            <p className="font-medium text-slate-200">
              {alert.dbscan_score.toFixed(2)} / {alert.classifier_score.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="mb-2 text-sm font-medium text-slate-300">Why was this flagged?</h2>
        <p className="text-sm leading-relaxed text-slate-400">{alert.narrative}</p>
      </div>

      <div className="card p-6">
        <h2 className="mb-4 text-sm font-medium text-slate-300">How the risk score was composed</h2>
        <SignalBreakdown breakdown={alert.signal_breakdown} />
      </div>

      <div className="card p-6">
        <h2 className="mb-2 text-sm font-medium text-slate-300">Feature Impact (SHAP)</h2>
        <ShapBarChart explanation={alert.shap_explanation} />
      </div>
    </div>
  );
}
