---
id: FE-00
title: Monorepo & Frontend Project Setup
tag: done
epic: Foundation
phase: Phase 3 — Chat UI
prd_refs: [FR-1, §6.1]
arch_refs: [§3.1, §7]
nextjs_version: "16.x"
created: 2026-06-04
---

# FE-00 — Monorepo & Frontend Project Setup

## Story
As a developer, I want the Next.js frontend scaffolded inside the shared monorepo so that the UI is set up with shadcn/ui (light theme) and ready to consume the backend.

## Context
The project uses a **monorepo** holding both the Next.js frontend and the FastAPI backend (Architecture §3, §7). The frontend is a pure client of the backend — it holds no secrets (§3.1).

**Runtime:** Next.js **16.x** (App Router).

## Acceptance Criteria
- [ ] Next.js **16.x** (App Router) app created at `apps/frontend/` inside the monorepo (coordinated with [[BE-00 Monorepo and Backend Project Setup]] on the repo root).
- [ ] **shadcn/ui** initialised with the **light theme** (project UI convention, FR-1).
- [ ] Organised by **vertical slice** (`app/features/chat/`) — components, hooks, API client, types co-located (Architecture §3.1).
- [ ] Backend base URL configured via environment variable (no secrets in client code — NFR-1).
- [ ] ESLint + Prettier configured; `next dev` runs and renders a placeholder page.

## Dependencies
- Coordinates with [[BE-00 Monorepo and Backend Project Setup]] on shared monorepo root.
