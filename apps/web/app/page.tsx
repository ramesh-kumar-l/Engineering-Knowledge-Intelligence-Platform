import Link from "next/link";
import { Suspense } from "react";

import { SystemStatus } from "@/components/system-status";

// Always render fresh: readiness reflects live datastore state.
export const dynamic = "force-dynamic";

export default function OverviewPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Overview</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Phase 1 — Knowledge Ingestion is live. Configure sources and run syncs from{" "}
          <Link href="/connectors" className="text-primary hover:underline">
            Connectors
          </Link>
          . Knowledge graph, retrieval, trust, and the assistant arrive in later phases.
        </p>
      </div>
      <Suspense fallback={<StatusSkeleton />}>
        <SystemStatus />
      </Suspense>
    </div>
  );
}

function StatusSkeleton() {
  return (
    <div className="h-40 animate-pulse rounded-lg border border-border bg-card" aria-hidden />
  );
}
