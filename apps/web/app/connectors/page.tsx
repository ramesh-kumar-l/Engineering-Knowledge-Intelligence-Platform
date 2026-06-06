import Link from "next/link";

import { createConnectorAction } from "@/app/connectors/actions";
import { Badge } from "@/components/badge";
import { fetchCatalog, fetchConnectors } from "@/lib/api";
import { connectorTone, formatDate } from "@/lib/format";

// Connector data reflects live ingestion state.
export const dynamic = "force-dynamic";

export default async function ConnectorsPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const [connectors, catalog] = await Promise.all([
    fetchConnectors(),
    fetchCatalog(),
  ]);

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Connectors</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Connect knowledge sources and run incremental syncs. (Phase 1 — Ingestion)
        </p>
      </div>

      {searchParams.error ? (
        <p
          role="alert"
          className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
        >
          {searchParams.error}
        </p>
      ) : null}

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Configured connectors</h3>
        {connectors.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No connectors yet. Add a GitHub repository below to start ingesting.
          </p>
        ) : (
          <ul className="mt-4 divide-y divide-border">
            {connectors.map((c) => (
              <li key={c.id} className="flex items-center justify-between py-3">
                <div className="min-w-0">
                  <Link
                    href={`/connectors/${c.id}`}
                    className="text-sm font-medium hover:underline"
                  >
                    {c.name}
                  </Link>
                  <p className="text-xs text-muted-foreground">
                    {c.source_type} · last synced {formatDate(c.last_synced_at)}
                  </p>
                </div>
                <Badge tone={connectorTone(c.status)} label={c.status} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Add a GitHub connector</h3>
        <form action={createConnectorAction} className="mt-4 grid gap-3 sm:grid-cols-2">
          <Field name="name" label="Name" placeholder="Platform issues" />
          <Field name="owner" label="Repository owner" placeholder="acme" />
          <Field name="repo" label="Repository name" placeholder="platform" />
          <Field name="secret" label="Access token" type="password" placeholder="ghp_…" />
          <div className="sm:col-span-2">
            <button
              type="submit"
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
            >
              Add connector
            </button>
          </div>
        </form>
      </section>

      <section>
        <h3 className="text-sm font-semibold">Source catalog</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {catalog.map((source) => (
            <div
              key={source.source_type}
              className="rounded-lg border border-border bg-card p-4"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{source.label}</span>
                <Badge
                  tone={source.implemented ? "success" : "muted"}
                  label={source.implemented ? "Available" : "Coming soon"}
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{source.description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Field({
  name,
  label,
  placeholder,
  type = "text",
}: {
  name: string;
  label: string;
  placeholder?: string;
  type?: string;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-muted-foreground">{label}</span>
      <input
        name={name}
        type={type}
        placeholder={placeholder}
        required
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
      />
    </label>
  );
}
