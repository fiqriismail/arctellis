---
id: FE-09
title: Deploy to Azure Static Web Apps
tag: done
epic: Deploy
phase: Phase 5 — Deploy
prd_refs:
  - §6.1
  - D-5
arch_refs:
  - §7
created: 2026-06-04
---

# FE-09 — Deploy to Azure Static Web Apps

## Story
As the team, I want the frontend deployed to Azure Static Web Apps so that users can reach the chat UI in production.

## Context
The frontend hosts on Azure Static Web Apps as a pure client of the backend; it holds no secrets (Architecture §7, PRD §6.1, D-5).

## Acceptance Criteria
- [ ] Next.js frontend deployed to **Azure Static Web Apps** (D-5).
- [ ] Backend base URL and Entra config supplied via environment, not committed secrets (NFR-1).
- [ ] CI builds and deploys the frontend from the monorepo.
- [ ] Smoke test: sign in, ask a question, see a streamed answer end-to-end (Phase 5).

## Dependencies
- [[FE-04 SSE Streaming and Loading Indicator]]
- [[FE-07 Entra Sign-in and Auth Gate]]
- Backend: [[BE-12 Key Vault Secrets and Deployment]]
