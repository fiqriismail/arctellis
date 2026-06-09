---
id: BE-07
title: Entra Token Validation Middleware
tag: done
epic: Agent Core
phase: Phase 2 — Agent core
prd_refs:
  - NFR-8
  - D-2
  - §6.4
arch_refs:
  - §6.1
  - §6.2
created: 2026-06-04
---

# BE-07 — Entra Token Validation Middleware

## Story
As the backend, I want to validate the end-user's Entra ID token on every request so that only authenticated organisation members can use the app.

## Context
The Next.js ↔ FastAPI boundary is the trust boundary (Architecture §6.1). End-user sign-in governs *access to the app* and is distinct from the app's own client-credentials read identity ([[BE-01 Entra App Registration and Graph Auth]]).

## Acceptance Criteria
- [ ] Backend validates the Entra ID bearer token on **every** request (NFR-8).
- [ ] Unauthenticated/invalid requests are rejected (401) — no anonymous access (D-2).
- [ ] Token validation (issuer/audience/signature/expiry) implemented correctly.
- [ ] Applied as middleware/dependency across protected routes (incl. `/chat`).
- [ ] No secrets or data returned to unauthenticated callers (NFR-2).

## Dependencies
- [[BE-00 Monorepo and Backend Project Setup]]
- Coordinates with [[FE-07 Entra Sign-in and Auth Gate]]
