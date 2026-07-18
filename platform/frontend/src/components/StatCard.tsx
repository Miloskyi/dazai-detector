import type { LucideIcon } from "lucide-react";

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "default" | "critical";
}) {
  return (
    <div className="card flex items-center gap-4 p-4">
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
          tone === "critical" ? "bg-tier-critical/10 text-tier-critical" : "bg-accent-600/10 text-accent-400"
        }`}
      >
        <Icon size={18} />
      </div>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="mt-0.5 text-xl font-semibold text-white">{value}</p>
      </div>
    </div>
  );
}
