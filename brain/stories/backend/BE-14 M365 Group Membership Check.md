---
id: BE-14
title: M365 Group Membership Check
tag: done
epic: Access Control
phase: Phase 6 — Access Control
prd_refs: []
arch_refs: []
created: 2026-06-24
---

# BE-14 — M365 Group Membership Check

## Story
As the system, I want to restrict backend access to members of a configured M365 group so that only authorised users can use the application.

## Context
Currently any valid Entra ID token grants access. This story restricts access to users holding a specific Entra app role, assigned to the allowed M365 group. The `roles` claim is injected by Entra into every JWT automatically — no Graph API call is needed.

**Implementation note:** Original approach used `checkMemberObjects`/`transitiveMemberOf` via Graph API but both require `Directory.Read.All` in practice (despite docs listing `GroupMember.Read.All`). Switched to app role approach: define role `App.Access` on the app registration, assign the M365 group to that role in Enterprise Applications. Backend reads the `roles` JWT claim — zero Graph permissions needed for access control.

## Acceptance Criteria
- [x] `ALLOWED_ROLE` added to `Settings` with default `"App.Access"`.
- [x] `require_group_member` FastAPI dependency wraps `require_auth`: returns `401` on invalid token, `403` if `allowed_role` absent from `roles` claim.
- [x] `GET /access` endpoint returns `200` for role holders, `403` for others.
- [x] `/chat` router updated to use `require_group_member`.
- [x] Tests: role present → passes, role absent → 403, no roles claim → 403.

## Dependencies
- [[BE-07 Entra Token Validation Middleware]]
- [[BE-01 Entra App Registration and Graph Auth]]
