# FE-07 — Entra Sign-in & Auth Gate: Design Spec

**Date:** 2026-06-05
**Story:** FE-07 Entra Sign-in & Auth Gate
**Status:** Approved

---

## Overview

Gate the entire chat UI behind Entra ID authentication. Unauthenticated users see a centred sign-in card; authenticated users see the normal app. A `useToken` hook exposes token acquisition for backend requests (consumed by FE-08).

---

## Architecture & File Structure

New `features/auth/` vertical slice plus targeted changes to two existing files:

```
features/auth/
  msalConfig.ts                   — PublicClientApplication instance (reads env vars)
  components/
    SignInCard.tsx                 — presentational sign-in card (brand, button)
    AuthGate.tsx                  — auth state check; renders SignInCard or children
  hooks/
    useToken.ts                   — silent → popup token acquisition; returns getToken()

app/layout.tsx                    — add MsalProvider wrapping children
app/page.tsx                      — wrap content in <AuthGate>
```

**Package additions:** `@azure/msal-browser` and `@azure/msal-react`.

**New test files:**
```
__tests__/SignInCard.test.tsx
__tests__/AuthGate.test.tsx
__tests__/useToken.test.ts
```

---

## Environment Variables

Add to `.env.local` (never committed — already gitignored):

```
NEXT_PUBLIC_ENTRA_CLIENT_ID=<app-registration-client-id>
NEXT_PUBLIC_ENTRA_TENANT_ID=<tenant-id>
NEXT_PUBLIC_ENTRA_API_SCOPE=api://<client-id>/access_as_user
```

Create `apps/frontend/.env.local.example` (new file, committed to git) with the same keys but empty values, so developers know what to set.

---

## Component Details

### `msalConfig.ts`

Creates and exports a single `PublicClientApplication` instance at module level (outside any component to avoid re-creation on re-renders):

```ts
import { PublicClientApplication } from '@azure/msal-browser'

export const msalInstance = new PublicClientApplication({
  auth: {
    clientId: process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.NEXT_PUBLIC_ENTRA_TENANT_ID}`,
    redirectUri: typeof window !== 'undefined' ? window.location.origin : '/',
  },
  cache: { cacheLocation: 'sessionStorage', storeAuthStateInCookie: false },
})
```

### `SignInCard.tsx`

Pure presentational component — no MSAL dependency:

```tsx
interface SignInCardProps {
  onSignIn: () => void
}
```

Renders: brand icon (Sparkles, matching the landing page), app title, tagline "Sign in with your organisation account to continue.", and a primary "Sign in with Microsoft" button that calls `onSignIn`. Styled with CSS variables (`var(--brand)`, `var(--background)`, etc.) — no hard-coded colours.

### `AuthGate.tsx`

```tsx
interface AuthGateProps {
  children: React.ReactNode
}
```

Uses `useIsAuthenticated()` and `useMsal()` from `@azure/msal-react`:
- If authenticated → render `{children}`
- If not authenticated → render `<SignInCard onSignIn={handleSignIn} />`

`handleSignIn` calls:
```ts
instance.loginPopup({
  scopes: [process.env.NEXT_PUBLIC_ENTRA_API_SCOPE!]
})
```

### `useToken.ts`

```ts
export function useToken(): { getToken: () => Promise<string> }
```

`getToken()` implementation:
1. Call `instance.acquireTokenSilent({ scopes: [SCOPE], account: accounts[0] })`
2. Return `response.accessToken`
3. If `InteractionRequiredAuthError` is thrown, fall back to `instance.acquireTokenPopup({ scopes: [SCOPE] })` and return its `accessToken`

This handles session expiry transparently — the user is re-prompted automatically.

### `app/layout.tsx`

Import `MsalProvider` from `@azure/msal-react` and `msalInstance` from `features/auth/msalConfig`. Wrap `{children}` with `<MsalProvider instance={msalInstance}>`. Must be a Client Component (`'use client'`).

### `app/page.tsx`

Import `AuthGate` and wrap the entire `HomePage` return with `<AuthGate>...</AuthGate>`. No other changes.

---

## Testing

All tests mock `@azure/msal-react` at the module level — no real Entra ID calls.

### `SignInCard.test.tsx`
| Test | Description |
|---|---|
| Renders brand title | "List AI Assistant" visible |
| Renders sign-in button | "Sign in with Microsoft" button present |
| Click calls onSignIn | `onSignIn` handler called once on click |

### `AuthGate.test.tsx`

Mock `useIsAuthenticated` and `useMsal` from `@azure/msal-react`:

| Test | Description |
|---|---|
| Unauthenticated → shows SignInCard | SignInCard rendered, children absent |
| Authenticated → shows children | Children rendered, SignInCard absent |
| Sign-in button calls loginPopup | `instance.loginPopup` called with correct scope |

### `useToken.test.ts`

Mock `useMsal`:

| Test | Description |
|---|---|
| Returns token on silent success | `getToken()` resolves to access token string |
| Falls back to popup on InteractionRequiredAuthError | `acquireTokenPopup` called when silent throws |

---

## Constraints

- **Popup only** — `loginPopup` and `acquireTokenPopup` throughout; no redirect flow.
- **`sessionStorage` cache** — token not persisted across browser restarts; re-login required per session.
- **No secrets in client** — `NEXT_PUBLIC_` vars contain only Client ID, Tenant ID, and scope — all are public registration values.
- **`useToken` is consumed by FE-08** — not wired into `streamMessage` in this story; just implemented and exported.
- **Existing tests unchanged** — `page.test.tsx` and others mock MSAL at module level; `AuthGate` is transparent to them.
