import type { SignalBreakdown as SignalBreakdownType } from "../types";

function SignalRow({
  label,
  score,
  weight,
  contribution,
  color,
}: {
  label: string;
  score: number;
  weight: number;
  contribution: number;
  color: string;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between text-xs text-slate-400">
        <span>
          {label} <span className="text-slate-600">· weight {weight.toFixed(1)}</span>
        </span>
        <span className="tabular-nums text-slate-300">
          {score.toFixed(2)} → contributes {contribution.toFixed(2)}
        </span>
      </div>
      <div className="mt-1.5 h-2 w-full rounded-full bg-white/[0.06]">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(contribution, 1) * 100}%` }} />
      </div>
    </div>
  );
}

export function SignalBreakdown({ breakdown }: { breakdown: SignalBreakdownType }) {
  return (
    <div className="space-y-4">
      <SignalRow
        label="Supervised classifier (XGBoost)"
        score={breakdown.classifier.score}
        weight={breakdown.classifier.weight}
        contribution={breakdown.classifier.contribution}
        color="bg-accent-500"
      />
      <SignalRow
        label="DBSCAN anomaly signal"
        score={breakdown.dbscan.score}
        weight={breakdown.dbscan.weight}
        contribution={breakdown.dbscan.contribution}
        color="bg-teal-400"
      />
      <div className="flex items-center justify-between border-t border-white/[0.06] pt-3 text-sm">
        <span className="text-slate-400">Final risk score</span>
        <span className="font-semibold text-white">{breakdown.risk_score.toFixed(2)}</span>
      </div>
    </div>
  );
}
