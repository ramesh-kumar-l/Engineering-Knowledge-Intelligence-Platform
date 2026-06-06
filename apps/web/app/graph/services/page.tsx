import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchGraphEntities } from "@/lib/api";
import { entityKindTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ServiceExplorerPage() {
  const services = await fetchGraphEntities("service");

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/graph" className="text-xs text-muted-foreground hover:underline">
        ← Knowledge Graph
      </Link>

      <div>
        <h2 className="text-lg font-semibold tracking-tight">Service explorer</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Services and their dependencies. Declare them on the{" "}
          <Link href="/graph/dependencies" className="text-primary hover:underline">
            dependency graph
          </Link>
          .
        </p>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        {services.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No services yet. Add a dependency to register services.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {services.map((service) => (
              <li
                key={service.key}
                className="flex items-center justify-between gap-3 py-3"
              >
                <Link
                  href={`/graph/entity?key=${encodeURIComponent(service.key)}`}
                  className="min-w-0 truncate text-sm font-medium hover:underline"
                >
                  {service.name}
                </Link>
                <Badge tone={entityKindTone(service.kind)} label={service.kind} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
