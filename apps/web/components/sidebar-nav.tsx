"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";

/**
 * Primary navigation. Enabled entries are links; the active one is derived from the
 * current path. Disabled entries are placeholders for screens in later phases.
 */
const NAV_ITEMS = [
  { label: "Overview", href: "/", enabled: true },
  { label: "Connectors", href: "/connectors", enabled: true },
  { label: "Sync", href: "/sync", enabled: true },
  { label: "Processing", href: "/processing", enabled: true },
  { label: "Knowledge Graph", href: "/graph", enabled: true },
  { label: "Search", href: "/search", enabled: true },
  { label: "Trust", href: "/trust", enabled: true },
  { label: "Assistant", href: "/assistant", enabled: true },
  { label: "Intelligence", href: "/intelligence", enabled: true },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <nav className="space-y-1" aria-label="Primary">
      {NAV_ITEMS.map((item) => {
        const active = item.enabled && isActive(pathname, item.href);
        if (!item.enabled) {
          return (
            <span
              key={item.label}
              aria-disabled
              className="block rounded-md px-3 py-2 text-sm text-muted-foreground/50"
            >
              {item.label}
            </span>
          );
        }
        return (
          <Link
            key={item.label}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={
              active
                ? "block rounded-md bg-muted px-3 py-2 text-sm text-foreground"
                : "block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted"
            }
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
