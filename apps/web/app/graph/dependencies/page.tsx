import Link from "next/link";

import { addRelationshipAction } from "@/app/graph/actions";
import { fetchGraphRelationships } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DependencyGraphPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const dependencies = await fetchGraphRelationships("depends_on");

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/graph" className="text-xs text-muted-foreground hover:underline">
        ← Knowledge Graph
      </Link>

      <div>
        <h2 className="text-lg font-semibold tracking-tight">Dependency graph</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Service and repository dependencies. Declare a dependency below — endpoints are
          created automatically.
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
        <h3 className="text-sm font-semibold">Add dependency</h3>
        <form
          action={addRelationshipAction}
          className="mt-4 flex flex-wrap items-end gap-3"
        >
          <input type="hidden" name="type" value="depends_on" />
          <input type="hidden" name="from_kind" value="service" />
          <input type="hidden" name="to_kind" value="service" />
          <Field name="from_name" label="Service" placeholder="checkout" />
          <span className="pb-2 text-sm text-muted-foreground">depends on</span>
          <Field name="to_name" label="Dependency" placeholder="payments" />
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Add
          </button>
        </form>
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Dependencies ({dependencies.length})</h3>
        {dependencies.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No dependencies declared yet.
          </p>
        ) : (
          <ul className="mt-4 space-y-2 text-sm">
            {dependencies.map((dep) => (
              <li
                key={`${dep.from_key}->${dep.to_key}`}
                className="flex items-center gap-2"
              >
                <Link
                  href={`/graph/entity?key=${encodeURIComponent(dep.from_key)}`}
                  className="font-medium hover:underline"
                >
                  {dep.from_name ?? dep.from_key}
                </Link>
                <span className="text-muted-foreground">depends on</span>
                <Link
                  href={`/graph/entity?key=${encodeURIComponent(dep.to_key)}`}
                  className="font-medium hover:underline"
                >
                  {dep.to_name ?? dep.to_key}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Field({
  name,
  label,
  placeholder,
}: {
  name: string;
  label: string;
  placeholder: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-muted-foreground">
      {label}
      <input
        name={name}
        placeholder={placeholder}
        required
        className="rounded-md border border-border bg-background px-2 py-1.5 text-sm text-foreground"
      />
    </label>
  );
}
