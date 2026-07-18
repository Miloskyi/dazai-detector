import type { LucideIcon } from "lucide-react";

export function EmptyState({ icon: Icon, message }: { icon: LucideIcon; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 p-12 text-center text-slate-500">
      <Icon size={28} className="text-slate-600" />
      <p className="text-sm">{message}</p>
    </div>
  );
}
