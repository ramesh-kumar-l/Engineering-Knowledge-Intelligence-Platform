"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import type { EntityKind, RelationshipType } from "@ekip/contracts";

import {
  createGraphRelationship,
  triggerGraphBuild,
} from "@/lib/api";

/** Project ingested data into the knowledge graph, then refresh the explorer. */
export async function buildGraphAction(): Promise<void> {
  const result = await triggerGraphBuild();
  revalidatePath("/graph");
  if (!result.ok) {
    redirect(`/graph?error=${encodeURIComponent(result.error ?? "Build failed")}`);
  }
  redirect("/graph");
}

/** Curate a relationship (and its endpoints) from the Dependency Graph form. */
export async function addRelationshipAction(formData: FormData): Promise<void> {
  const fromName = String(formData.get("from_name") ?? "").trim();
  const toName = String(formData.get("to_name") ?? "").trim();
  const type = String(formData.get("type") ?? "depends_on") as RelationshipType;
  const fromKind = String(formData.get("from_kind") ?? "service") as EntityKind;
  const toKind = String(formData.get("to_kind") ?? "service") as EntityKind;

  if (!fromName || !toName) {
    redirect("/graph/dependencies?error=Both+names+are+required");
  }

  const result = await createGraphRelationship({
    type,
    from_kind: fromKind,
    from_name: fromName,
    to_kind: toKind,
    to_name: toName,
  });
  revalidatePath("/graph/dependencies");
  if (!result.ok) {
    redirect(`/graph/dependencies?error=${encodeURIComponent(result.error ?? "Failed")}`);
  }
  redirect("/graph/dependencies");
}
