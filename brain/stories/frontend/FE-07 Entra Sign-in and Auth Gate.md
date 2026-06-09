---
id: FE-07
title: Entra Sign-in & Auth Gate
tag: done
epic: Chat UI
phase: Phase 3 — Chat UI
prd_refs:
  - NFR-8
  - D-2
  - §6.4
arch_refs:
  - §6.1
  - §6.2
created: 2026-06-04
---

# FE-07 — Entra Sign-in & Auth Gate

## Story
As an organisation member, I want to sign in with Entra ID before using the app so that only authenticated users can access it, and my token authorises my backend requests.

## Context
End users authenticate in the Next.js app; the backend validates the token on every request (PRD §6.4, NFR-8). The frontend never holds Graph or Azure OpenAI credentials — the FE↔BE boundary is the trust boundary (Architecture §6.1).

## Acceptance Criteria
- [ ] Users sign in with **Entra ID**; unauthenticated users cannot reach the chat (NFR-8, D-2).
- [ ] The acquired token is attached to backend requests (bearer) for validation by [[BE-07 Entra Token Validation Middleware]].
- [ ] No Graph/Azure OpenAI credentials ever held in the client (NFR-1, §6.4).
- [ ] Sign-out / session expiry handled (re-prompt to authenticate).

## Dependencies
- [[FE-00 Monorepo and Frontend Project Setup]]
- Backend: [[BE-07 Entra Token Validation Middleware]]
