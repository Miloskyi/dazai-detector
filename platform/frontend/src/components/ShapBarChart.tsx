import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ShapFeature } from "../types";

export function ShapBarChart({ explanation }: { explanation: ShapFeature[] }) {
  const data = [...explanation]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .map((f) => ({ name: f.feature, impact: f.shap_value }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical" margin={{ left: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0f" horizontal={false} />
        <XAxis type="number" stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 12 }} />
        <YAxis type="category" dataKey="name" width={60} stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 12 }} />
        <Tooltip
          contentStyle={{ background: "#131318", border: "1px solid #ffffff1a", borderRadius: 12 }}
          labelStyle={{ color: "#e2e8f0" }}
          itemStyle={{ color: "#e2e8f0" }}
        />
        <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.impact > 0 ? "#ef4444" : "#22c55e"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
