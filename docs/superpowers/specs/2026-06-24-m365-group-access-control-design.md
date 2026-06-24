# M365 Group Access Control — Design Spec

**Date:** 2026-06-24  
**Status:** Approved

## Overview

Restrict access to the RTP Intelligent Hub to members of a specific Microsoft 365 Group. Any user who signs in with a valid Entra ID account but is not a member of the configured group is denied access with a friendly UI. Group membership is enforced on both the backend (authoritative) and the frontend (UX).

---

## Backend

### Configuration

Add `ALLOWED_GROUP_ID` to `config.py` Settings — the Entra Object ID of the M365 group.

```
ALLOWED_GROUP_ID=<m365-group-object-id>
```

### Graph Permission

The backend app registration requires `GroupMember.Read.All` added to its existing Microsoft Graph application permissions (and admin-consented).

### Group Membership Module — `group_auth.py`

New module at `apps/backend/src/app/group_auth.py` with two responsibilities:

**1. Membership check via Graph**  
Calls `POST /v1.0/users/{oid}/checkMemberObjects` with the configured group ID. Returns `True` if the user is a member, `False` otherwise. Uses the existing `GraphAuthService` client (client-credentials flow). The user is identified by their Entra Object ID (`oid` claim from the JWT) — not UPN or email — so aliases and UPN changes are handled correctly.

**2. In-memory cache**  
A `dict[str, tuple[bool, float]]` keyed by `oid`. Each entry stores `(is_member, expiry_timestamp)`. TTL is 5 minutes. On each check: return cached result if `time.time() < expiry`, otherwise call Graph and store the result. Means a removed user stays active for up to 5 minutes before being denied.

### FastAPI Dependency

A new `require_group_member` dependency in `auth.py` wraps the existing `require_auth`:
1. Calls `require_auth` to validate the JWT — returns `401` if invalid.
2. Extracts the `oid` claim from the decoded token.
3. Calls `check_group_membership(oid)` — returns `403 Forbidden` if not a member.
4. Returns the decoded claims to the route handler.

The `/chat` router dependency is updated from `require_auth` to `require_group_member`.

### New Endpoint — `GET /access`

A lightweight endpoint that runs `require_group_member` and returns `200 OK`. No request body, no response body. Purpose: gives the frontend a dedicated probe to check access without coupling it to the chat endpoint.

---

## Frontend

### Auth Flow Change

`AuthGate` currently renders the chat once an MSAL account exists. The updated flow:

1. User signs in → MSAL account exists
2. `AuthGate` calls a new `useGroupAccess` hook
3. Hook calls `GET /access` with the Bearer token
4. **Loading:** show spinner (reuse existing loading state)
5. **200:** render chat as normal
6. **403:** render `UnauthorizedCard`

### `useGroupAccess` Hook

`src/features/auth/hooks/useGroupAccess.ts`

- Uses `useToken()` to acquire the access token silently
- Calls `GET /access` on mount (once per session; result is held in local state)
- Returns `{ status: 'loading' | 'authorized' | 'unauthorized' }`

### `UnauthorizedCard` Component

`src/features/auth/components/UnauthorizedCard.tsx`

Renders within `AuthGate` when access is denied:
- RTP logo (consistent with `SignInCard`)
- Message: "You don't have access to this application"
- Signed-in user's display name and email (from MSAL `account` object)
- Sign-out button — calls `instance.logoutPopup()`

### New API Function

`src/features/chat/api/checkAccess.ts` (or within the auth feature API layer) — thin function that calls `GET /access` and returns `true` (200) or `false` (403).

---

## Error Handling

| Scenario | Backend | Frontend |
|---|---|---|
| Valid token, in group | 200 | Render chat |
| Valid token, not in group | 403 | Render `UnauthorizedCard` |
| Invalid/expired token | 401 | MSAL acquires new token or prompts sign-in |
| Graph call fails (transient) | 503 / 500 | Frontend treats non-200/403 as transient error, retries once, then shows generic error state |
| `ALLOWED_GROUP_ID` not configured | Backend startup error (fail fast) | — |

---

## Stories

| ID | Title | Layer |
|---|---|---|
| BE-14 | M365 Group Membership Check — Backend | Backend |
| FE-14 | M365 Group Access Gate — Frontend | Frontend |

### BE-14 — M365 Group Membership Check

- Add `ALLOWED_GROUP_ID` to Settings; fail fast on startup if missing
- Add `GroupMember.Read.All` to Graph permissions (documented in setup guide)
- Implement `group_auth.py` with Graph check + 5-min TTL cache
- Add `require_group_member` dependency wrapping `require_auth`
- Add `GET /access` endpoint
- Update `/chat` router to use `require_group_member`
- Tests: cache hit/miss, group member returns 200, non-member returns 403, Graph failure returns 503

### FE-14 — M365 Group Access Gate

- Implement `useGroupAccess` hook calling `GET /access`
- Implement `UnauthorizedCard` component (logo, message, user info, sign-out)
- Update `AuthGate` to include loading → authorized/unauthorized states
- Add `checkAccess` API function
- Tests: authorized user sees chat, unauthorized user sees `UnauthorizedCard`, loading state renders correctly

---

## Environment Variables

| Variable | Layer | Description |
|---|---|---|
| `ALLOWED_GROUP_ID` | Backend | Entra Object ID of the M365 group |

No new frontend env vars — the frontend defers entirely to the backend for the authoritative access decision.
