import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "EKIP — Engineering Knowledge Intelligence Platform",
  description: "The trusted engineering memory and intelligence layer.",
};

// Dark-mode-first (ui_design_system.md): the dark class is applied at the root.
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
