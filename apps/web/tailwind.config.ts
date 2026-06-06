import type { Config } from "tailwindcss";

/**
 * Tailwind theme (ADR-0003, ui_design_system.md). Dark mode is the default token
 * set; tokens are CSS variables defined in app/globals.css so backend-driven and
 * frontend rendering can stay consistent (shadcn/ui-compatible token shape).
 */
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: "hsl(var(--card))",
        muted: "hsl(var(--muted))",
        "muted-foreground": "hsl(var(--muted-foreground))",
        border: "hsl(var(--border))",
        primary: "hsl(var(--primary))",
        success: "hsl(var(--success))",
        danger: "hsl(var(--danger))",
      },
      borderRadius: {
        lg: "var(--radius)",
      },
    },
  },
  plugins: [],
};

export default config;
