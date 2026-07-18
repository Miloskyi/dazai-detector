const TIER_STYLES: Record<string, string> = {
  LOW: "bg-tier-low/10 text-tier-low ring-tier-low/25",
  MEDIUM: "bg-tier-medium/10 text-tier-medium ring-tier-medium/25",
  HIGH: "bg-tier-high/10 text-tier-high ring-tier-high/25",
  CRITICAL: "bg-tier-critical/10 text-tier-critical ring-tier-critical/25",
};

export function TierBadge({ tier }: { tier: string }) {
  const style = TIER_STYLES[tier] ?? "bg-white/5 text-slate-300 ring-white/10";
  return <span className={`pill ${style}`}>{tier}</span>;
}
