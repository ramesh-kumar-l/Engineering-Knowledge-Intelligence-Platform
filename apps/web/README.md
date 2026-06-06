# EKIP Web

Next.js (App Router) + React + TypeScript frontend (ADR-0003). Dark-mode-first,
Tailwind-tokenized design system (`ui_design_system.md`).

## Layout

```
app/
├── layout.tsx       # root layout + App Shell, dark theme
├── page.tsx         # Overview (system status)
└── globals.css      # design tokens (dark-first) + Tailwind layers
components/
├── app-shell.tsx    # sidebar + header frame
├── system-status.tsx# end-to-end: fetches API readiness
└── status-badge.tsx # trust-UX badge precursor
lib/
├── api.ts           # typed API client (uses @ekip/contracts)
└── utils.ts
```

The Overview screen is the walking-skeleton's end-to-end proof: a server component
fetches `GET /health/ready` from the API and renders backend + datastore health.

## Develop

```bash
npm install
cp .env.example .env.local   # set EKIP_API_URL (default http://localhost:8000)
npm run dev                  # http://localhost:3000
```

## Quality gates

```bash
npm run lint        # ESLint (next/core-web-vitals)
npm run typecheck   # tsc --noEmit (strict)
npm run build       # production build
```
