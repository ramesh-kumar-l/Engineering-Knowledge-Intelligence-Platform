import type { ReactNode } from "react";

import { SidebarNav } from "@/components/sidebar-nav";

/**
 * Application shell: persistent sidebar + header frame that all screens render
 * inside (screen_inventory.md "App Shell", Phase 0). Navigation lives in
 * SidebarNav so it can highlight the active route.
 */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 border-r border-border bg-card p-4 md:block">
        <div className="mb-6 px-2 text-sm font-semibold tracking-tight">EKIP</div>
        <SidebarNav />
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center border-b border-border px-6">
          <h1 className="text-sm font-medium">Engineering Knowledge Intelligence Platform</h1>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
