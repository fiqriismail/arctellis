---
id: BE-01
title: Entra App Registration & Graph Auth
tag: done
epic: Foundation
phase: Phase 1 — Foundation
prd_refs: [§6.4, D-1, D-2]
arch_refs: [§6.2, §6.3]
created: 2026-06-04
---

# BE-01 — Entra App Registration & Graph Auth

## Story
As the backend, I want to authenticate to Microsoft Graph using a client-credentials identity so that I can read SharePoint data on the app's own behalf.

## Context
The app reads SharePoint via its **own client-credentials identity** (single shared read account in v1 — Architecture §6.2, D-1). This is distinct from end-user sign-in (see [[BE-07 Entra Token Validation Middleware]]).

## Acceptance Criteria
- [ ] Entra ID app registration created with a client secret (stored as config/secret, never committed).
- [ ] Graph application permission granted — prefer scoped `Sites.Selected` for the target site, else `Sites.Read.All` — **with admin consent** (§6.3).
- [ ] Backend acquires a Graph token via `azure-identity`/`msal` client-credentials flow.
- [ ] A verification script confirms a token is obtained and a simple Graph call succeeds (Phase 1 test harness).
- [ ] Credentials resolved from config (env/`.env` locally; Key Vault in deployment — see [[BE-12 Key Vault Secrets and Deployment]]).

## Dependencies
- [[BE-00 Monorepo and Backend Project Setup]]
