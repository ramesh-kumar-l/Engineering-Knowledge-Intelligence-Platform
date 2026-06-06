import { cn } from "@/lib/utils";

/**
 * Generic status badge with semantic tones. Extends the Phase 0 StatusBadge into a
 * reusable family for connector/sync states (ui_design_system.md trust-UX badges).
 */
export type Tone = "success" | "danger" | "warning" | "info" | "muted";

const TONES: Record<Tone, string> = {
  success: "bg-success/15 text-success",
  danger: "bg-danger/15 text-danger",
  warning: "bg-yellow-500/15 text-yellow-500",
  info: "bg-primary/15 text-primary",
  muted: "bg-muted text-muted-foreground",
};

export function Badge({ tone, label }: { tone: Tone; label: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium",
        TONES[tone],
      )}
    >
      <span aria-hidden className={cn("h-1.5 w-1.5 rounded-full", `bg-current`)} />
      {label}
    </span>
  );
}
