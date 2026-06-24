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
Currently any valid Entra ID token grants access. This story adds a group membership check using the Microsoft Graph API, keyed off the user's Entra Object ID (`oid` claim). See design spec: `docs/superpowers/specs/2026-06-24-m365-group-access-control-design.md`.

## Acceptance Criteria
- [x] `ALLOWED_GROUP_ID` added to `Settings`; app fails to start if missing.
- [x] `GroupMember.Read.All` Graph permission documented in `docs/guides/azure-entra-id-setup.md`.
- [x] `group_auth.py` implements `check_group_membership(oid)` using `POST /v1.0/users/{oid}/checkMemberObjects` via the existing Graph client.
- [x] In-memory cache per `oid` with 5-minute TTL.
- [x] `require_group_member` FastAPI dependency wraps `require_auth`: returns `401` on invalid token, `403` if not in group.
- [x] `GET /access` endpoint returns `200` for group members, `403` for non-members.
- [x] `/chat` router updated to use `require_group_member`.
- [x] Tests: cache hit/miss, member → 200, non-member → 403, Graph failure → 503.

## Dependencies
- [[BE-07 Entra Token Validation Middleware]]
- [[BE-01 Entra App Registration and Graph Auth]]
