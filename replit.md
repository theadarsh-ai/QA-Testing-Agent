# QA Testing Agent Workspace

## Overview

QA Testing Agent is a full-stack AI Visual Accessibility QA Agent. It analyzes website screenshots, detects WCAG 2.1 accessibility violations using Gemini multimodal vision, and autonomously generates executable browser DevTools fix commands.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)
- **AI**: Google Gemini 2.5 Flash via Replit AI Integrations
- **Frontend**: React + Vite + Tailwind + shadcn/ui

## Architecture

```
Frontend (React/Vite) → Express API → Gemini Vision AI → PostgreSQL
                                   ↘ LangGraph-style Agent Loop
                                     (Observe → Detect → Prioritize → Fix → Verify → Report)
```

## Structure

```text
artifacts-monorepo/
├── artifacts/
│   ├── designguard/            # React + Vite frontend (dark theme)
│   │   └── src/
│   │       ├── pages/          # Scan, Results, Fix Executor, History
│   │       ├── components/     # AppSidebar, ViolationBadge, CodeBlock
│   │       └── context/        # ScanContext for state sharing
│   └── api-server/             # Express API backend
│       └── src/routes/
│           ├── health.ts       # GET /api/healthz
│           └── designguard/
│               ├── index.ts    # Route handlers (scan, apply-fix, history)
│               ├── agent.ts    # LangGraph-style agent loop
│               ├── gemini-vision.ts  # Gemini multimodal analysis
│               └── fix-generator.ts  # DevTools command generator
├── lib/
│   ├── api-spec/               # OpenAPI spec + Orval codegen config
│   ├── api-client-react/       # Generated React Query hooks
│   ├── api-zod/                # Generated Zod schemas from OpenAPI
│   ├── db/                     # Drizzle ORM schema + DB connection
│   │   └── src/schema/
│   │       └── scans.ts        # Scans table
│   └── integrations-gemini-ai/ # Gemini AI client (Replit AI Integrations)
```

## API Endpoints

- `GET /api/healthz` — Health check
- `POST /api/scan` — Analyze screenshot, returns violations + fixes + scores
- `POST /api/apply-fix` — Get fix details for a specific violation
- `GET /api/history/:userId` — Last 10 scans for a user

## WCAG Violation Categories

1. COLOR_CONTRAST — Text/background contrast below 4.5:1 (AA)
2. FONT_SIZE — Text below 12px minimum
3. MISSING_ALT_TEXT — Images with no descriptive context
4. KEYBOARD_FOCUS — Interactive elements with no focus indicator
5. BUTTON_SIZE — Touch targets smaller than 44x44px
6. HEADING_STRUCTURE — Missing or illogical heading hierarchy
7. LINK_TEXT — Generic link text like 'click here'
8. FORM_LABELS — Input fields with no visible label

## Environment Variables

- `AI_INTEGRATIONS_GEMINI_BASE_URL` — Auto-set by Replit AI Integrations
- `AI_INTEGRATIONS_GEMINI_API_KEY` — Auto-set by Replit AI Integrations
- `DATABASE_URL` — Auto-set by Replit Database
