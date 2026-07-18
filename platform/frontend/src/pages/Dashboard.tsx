import { AlertTriangle, DollarSign, ShieldAlert, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "../api/client";
import { StatCard } from "../components/StatCard";
import type { StatsSummary } from "../types";

const tooltipStyle = {
  contentStyle: { background: "#131318", border: "1px solid #ffffff1a", borderRadius: 12 },
  labelStyle: { color: "#e2e8f0" },
  itemStyle: { color: "#e2e8f0" },
};

export default function Dashboard() {
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<StatsSummary>("/stats")
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-red-400">Failed to load stats: {error}</p>;
  if (!stats) return <p className="text-slate-500">Loading...</p>;

  const hourData = Object.entries(stats.by_hour).map(([hour, count]) => ({ hour, count }));
  const bucketData = Object.entries(stats.by_amount_bucket).map(([bucket, count]) => ({ bucket, count }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Alerts" value={stats.total_alerts} icon={ShieldAlert} />
        <StatCard
          label="Flagged Amount"
          value={`$${stats.total_flagged_amount.toLocaleString()}`}
          icon={DollarSign}
        />
        <StatCard label="Critical Tier" value={stats.tier_distribution.CRITICAL ?? 0} icon={AlertTriangle} tone="critical" />
        <StatCard label="High Tier" value={stats.tier_distribution.HIGH ?? 0} icon={ShieldCheck} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-4 text-sm font-medium text-slate-300">Alerts by Hour</h2>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={hourData}>
              <defs>
                <linearGradient id="hourFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0f" vertical={false} />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis allowDecimals={false} stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip {...tooltipStyle} />
              <Area type="monotone" dataKey="count" stroke="#8b5cf6" fill="url(#hourFill)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h2 className="mb-4 text-sm font-medium text-slate-300">Alerts by Amount Bucket</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={bucketData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0f" vertical={false} />
              <XAxis dataKey="bucket" stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis allowDecimals={false} stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
