import { AlertCircle, BarChart3, FileSearch, Search } from "lucide-react";

const AGENT_META: Record<string, { label: string; icon: typeof Search }> = {
  analyst: { label: "Analyst", icon: BarChart3 },
  investigator: { label: "Investigator", icon: Search },
  reporter: { label: "Reporter", icon: FileSearch },
  system: { label: "System", icon: AlertCircle },
};

export function AgentBadge({ agent }: { agent: string }) {
  const meta = AGENT_META[agent] ?? { label: agent, icon: Search };
  const Icon = meta.icon;

  return (
    <span className="pill bg-accent-600/10 text-accent-400 ring-accent-600/25">
      <Icon size={11} />
      {meta.label}
    </span>
  );
}
