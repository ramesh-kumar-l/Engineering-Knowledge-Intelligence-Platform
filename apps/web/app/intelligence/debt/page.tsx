import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchDebtIntel } from "@/lib/api";
import {
  confidenceTone,
  debtReasonLabel,
  formatAge,
  freshnessTone,
  riskTone,
} from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function TechnicalDebtPage() {
  const report = await fetchDebtIntel();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Technical Debt</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Documents carrying knowledge debt — low confidence, stale, or unowned —
            ranked by severity. Derived from the trust layer; fix by re-processing,
            refreshing the source, or assigning an owner. (Phase 7)
          </p>
        </div>
        <Link href="/intelligence" className="text-sm text-primary hover:underline">
          ← Intelligence
        </Link>
      </div>

      {report ? (
        <section className="grid grid-cols-3 gap-4">
          {Object.entries(report.by_reason).map(([reason, count]) => (
            <div key={reason} className="rounded-lg border border-border bg-card p-4">
              <p className="text-xs text-muted-foreground capitalize">
                {debtReasonLabel(reason)}
              </p>
              <p className="mt-1 text-2xl font-semibold">{count}</p>
            </div>
          ))}
        </section>
      ) : null}

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Debt items{" "}
          <span className="text-muted-foreground">
            ({report?.debt_count ?? 0} of {report?.total_documents ?? 0})
          </span>
        </h3>
        {!report || report.items.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No technical debt detected. Every document is fresh, confident and owned.
          </p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Document</th>
                <th className="pb-2 font-medium">Severity</th>
                <th className="pb-2 font-medium">Reasons</th>
                <th className="pb-2 font-medium">Confidence</th>
                <th className="pb-2 text-right font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {report.items.map((i) => (
                <tr key={i.document_id}>
                  <td className="py-3">
                    <Link
                      href={`/trust/documents/${i.document_id}`}
                      className="font-medium hover:underline"
                    >
                      {i.title}
                    </Link>
                  </td>
                  <td className="py-3">
                    <Badge
                      tone={riskTone(i.severity_band)}
                      label={`${i.severity_band} ${i.severity_score.toFixed(2)}`}
                    />
                  </td>
                  <td className="py-3">
                    <div className="flex flex-wrap gap-1">
                      {i.reasons.map((r) => (
                        <span
                          key={r}
                          className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground"
                        >
                          {debtReasonLabel(r)}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3">
                    <Badge
                      tone={confidenceTone(i.confidence_band)}
                      label={i.confidence_band}
                    />
                  </td>
                  <td className="py-3 text-right">
                    <Badge tone={freshnessTone(i.freshness_band)} label={formatAge(i.age_days)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
