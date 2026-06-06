import type { ReactNode } from "react";

/**
 * Application shell: persistent sidebar + header frame that all screens render
 * inside (screen_inventory.md "App Shell", Phase 0). Navigation entries are added
 * as the roadmap phases land.
 */
const NAV_ITEMS = [
  { label: "Overview", href: "/", active: true },
  { label: "Connectors", href: "#", active: false },
  { label: "Knowledge", href: "#", active: false },
  { label: "Search", href: "#", active: false },
  { label: "Assistant", href: "#", active: false },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 border-r border-border bg-card p-4 md:block">
        <div className="mb-6 px-2 text-sm font-semibold tracking-tight">EKIP</div>
        <nav className="space-y-1" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.label}
              href={item.href}
              aria-current={item.active ? "page" : undefined}
              aria-disabled={!item.active}
              className={
                item.active
                  ? "block rounded-md bg-muted px-3 py-2 text-sm text-foreground"
                  : "block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted"
              }
            >
              {item.label}
            </a>
          ))}
        </nav>
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
