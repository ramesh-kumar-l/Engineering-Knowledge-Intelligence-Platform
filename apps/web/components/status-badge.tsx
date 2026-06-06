import { cn } from "@/lib/utils";

/**
 * Status badge — a small, honest status indicator. A precursor to the trust-UX
 * badge family (freshness/confidence/ownership) defined in ui_design_system.md.
 */
export function StatusBadge({ healthy, label }: { healthy: boolean; label: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium",
        healthy ? "bg-success/15 text-success" : "bg-danger/15 text-danger",
      )}
    >
      <span
        aria-hidden
        className={cn("h-1.5 w-1.5 rounded-full", healthy ? "bg-success" : "bg-danger")}
      />
      {label}
    </span>
  );
}
