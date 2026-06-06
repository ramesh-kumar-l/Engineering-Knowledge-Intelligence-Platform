"use server";

import { redirect } from "next/navigation";

import type { AgentType } from "@ekip/contracts";

import { runAgent } from "@/lib/api";

/**
 * Launch an agent. Reads the agent type + optional target from the launcher form,
 * runs it server-side (the run + trace are persisted), then redirects to the Agent
 * Execution Viewer. Failures bounce back to the workspace with an error param.
 */
export async function runAgentAction(formData: FormData): Promise<void> {
  const agentType = String(formData.get("agent_type") ?? "") as AgentType;
  const target = String(formData.get("target") ?? "").trim();

  if (!agentType) {
    redirect(`/agents?error=${encodeURIComponent("Select an agent to run.")}`);
  }

  const result = await runAgent(agentType, target || undefined);
  if (!result) {
    redirect(
      `/agents?error=${encodeURIComponent("Agent run failed or the API is unavailable.")}`,
    );
  }

  redirect(`/agents/${result.run.id}`);
}
