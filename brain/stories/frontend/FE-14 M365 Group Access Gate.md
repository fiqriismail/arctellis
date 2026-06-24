---
id: FE-14
title: M365 Group Access Gate
tag: todo
epic: Access Control
phase: Phase 6 — Access Control
prd_refs: []
arch_refs: []
created: 2026-06-24
---

# FE-14 — M365 Group Access Gate

## Story
As an unauthorised user, I want to see a friendly "you don't have access" screen after signing in so that I understand why I cannot use the application and can sign out.

## Context
After sign-in, `AuthGate` will probe `GET /access` on the backend. A `403` response renders `UnauthorizedCard` instead of the chat. See design spec: `docs/superpowers/specs/2026-06-24-m365-group-access-control-design.md`.

## Acceptance Criteria
- [ ] `checkAccess()` API function calls `GET /access` with Bearer token, returns `true` (200) or `false` (403).
- [ ] `useGroupAccess` hook calls `checkAccess` on mount; returns `{ status: 'loading' | 'authorized' | 'unauthorized' }`.
- [ ] `UnauthorizedCard` component renders: RTP logo, denial message, signed-in user name + email, sign-out button.
- [ ] `AuthGate` updated: loading spinner while checking, chat on authorized, `UnauthorizedCard` on unauthorized.
- [ ] Transient errors (non-200, non-403) retry once then show generic error state.
- [ ] Tests: authorized → chat rendered, unauthorized → `UnauthorizedCard` rendered, loading state renders spinner.

## Dependencies
- [[FE-07 Entra Sign-in and Auth Gate]]
- [[FE-08 Backend API Client]]
- Backend: [[BE-14 M365 Group Membership Check]]
