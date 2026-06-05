# FE-07 Entra Sign-in & Auth Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate the chat UI behind Entra ID authentication using MSAL — unauthenticated users see a centred sign-in card, authenticated users access the app normally.

**Architecture:** `MsalProvider` lives in a new `app/Providers.tsx` client component (keeping `layout.tsx` as a server component for `metadata`). `AuthGate` checks auth state via MSAL hooks and renders either `SignInCard` or `children`. `useToken` exposes silent→popup token acquisition for FE-08 to consume.

**Tech Stack:** `@azure/msal-browser`, `@azure/msal-react`, React, Next.js App Router, Jest + Testing Library.

---

## File Map

| File | Change |
|---|---|
| `apps/frontend/src/features/auth/msalConfig.ts` | New — MSAL `PublicClientApplication` instance |
| `apps/frontend/src/features/auth/components/SignInCard.tsx` | New — pure sign-in UI |
| `apps/frontend/src/features/auth/components/AuthGate.tsx` | New — auth state gate |
| `apps/frontend/src/features/auth/hooks/useToken.ts` | New — token acquisition hook |
| `apps/frontend/src/app/Providers.tsx` | New — client component wrapping `MsalProvider` |
| `apps/frontend/src/app/layout.tsx` | Modify — import and use `Providers` |
| `apps/frontend/src/app/page.tsx` | Modify — wrap `HomePage` content in `AuthGate` |
| `apps/frontend/src/__tests__/SignInCard.test.tsx` | New — 3 unit tests |
| `apps/frontend/src/__tests__/AuthGate.test.tsx` | New — 3 unit tests |
| `apps/frontend/src/__tests__/useToken.test.ts` | New — 2 unit tests |
| `apps/frontend/src/__tests__/page.test.tsx` | Modify — add MSAL mock so AuthGate is transparent |
| `apps/frontend/.env.local.example` | New — env var keys with empty values |

> **Note on layout.tsx:** `layout.tsx` must stay a Server Component to export `metadata`. A separate `Providers.tsx` client component wraps `MsalProvider` — this is the standard Next.js App Router pattern.

---

## Task 1: Create and checkout feature branch

- [ ] **Step 1: Create and switch to the feature branch**

```bash
git checkout -b feature/FE-07-entra-auth-gate
```

Expected: `Switched to a new branch 'feature/FE-07-entra-auth-gate'`

---

## Task 2: Install MSAL packages

**Files:**
- Modify: `apps/frontend/package.json` (via npm install)

- [ ] **Step 1: Install packages**

```bash
cd apps/frontend && npm install @azure/msal-browser @azure/msal-react
```

Expected: packages appear in `dependencies` in `package.json`.

- [ ] **Step 2: Verify existing tests still pass**

```bash
cd apps/frontend && npm test -- --no-coverage
```

Expected: all 44 tests pass (packages added, no code changed).

- [ ] **Step 3: Commit**

```bash
git add apps/frontend/package.json apps/frontend/package-lock.json
git commit -m "chore(frontend): add @azure/msal-browser and @azure/msal-react (FE-07)"
```

---

## Task 3: SignInCard component (TDD)

**Files:**
- Create: `apps/frontend/src/__tests__/SignInCard.test.tsx`
- Create: `apps/frontend/src/features/auth/components/SignInCard.tsx`

- [ ] **Step 1: Create test file**

Create `apps/frontend/src/__tests__/SignInCard.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SignInCard } from '@/features/auth/components/SignInCard'

describe('SignInCard', () => {
  it('renders the app title', () => {
    render(<SignInCard onSignIn={() => {}} />)
    expect(screen.getByText('List AI Assistant')).toBeInTheDocument()
  })

  it('renders a Sign in with Microsoft button', () => {
    render(<SignInCard onSignIn={() => {}} />)
    expect(screen.getByRole('button', { name: /sign in with microsoft/i })).toBeInTheDocument()
  })

  it('calls onSignIn when the button is clicked', async () => {
    const user = userEvent.setup()
    const onSignIn = jest.fn()
    render(<SignInCard onSignIn={onSignIn} />)
    await user.click(screen.getByRole('button', { name: /sign in with microsoft/i }))
    expect(onSignIn).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd apps/frontend && npm test -- --testPathPattern=SignInCard --no-coverage
```

Expected: all 3 tests fail — module not found.

- [ ] **Step 3: Create `apps/frontend/src/features/auth/components/SignInCard.tsx`**

```tsx
import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SignInCardProps {
  onSignIn: () => void
}

export function SignInCard({ onSignIn }: SignInCardProps) {
  return (
    <div style={{
      height: '100dvh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--background)',
    }}>
      <div style={{
        width: '100%',
        maxWidth: 360,
        padding: '40px 32px',
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: 16,
        boxShadow: 'var(--shadow-card-md)',
        textAlign: 'center',
      }}>
        <div style={{
          width: 52,
          height: 52,
          borderRadius: 14,
          background: 'var(--brand)',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          boxShadow: 'var(--shadow-card-md)',
        }}>
          <Sparkles style={{ width: 26, height: 26 }} strokeWidth={2.1} />
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 680, letterSpacing: '-.02em', margin: '0 0 8px' }}>
          List AI Assistant
        </h1>
        <p style={{ fontSize: 14, color: 'var(--muted-foreground)', margin: '0 0 28px', lineHeight: 1.5 }}>
          Sign in with your organisation account to continue.
        </p>
        <Button onClick={onSignIn} style={{ width: '100%' }}>
          Sign in with Microsoft
        </Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests — verify GREEN**

```bash
cd apps/frontend && npm test -- --testPathPattern=SignInCard --no-coverage
```

Expected: all 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/features/auth/components/SignInCard.tsx \
        apps/frontend/src/__tests__/SignInCard.test.tsx
git commit -m "feat(frontend): add SignInCard component (FE-07)"
```

---

## Task 4: AuthGate + msalConfig (TDD)

**Files:**
- Create: `apps/frontend/src/__tests__/AuthGate.test.tsx`
- Create: `apps/frontend/src/features/auth/msalConfig.ts`
- Create: `apps/frontend/src/features/auth/components/AuthGate.tsx`

- [ ] **Step 1: Create test file**

Create `apps/frontend/src/__tests__/AuthGate.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthGate } from '@/features/auth/components/AuthGate'
import { useIsAuthenticated, useMsal } from '@azure/msal-react'

const mockLoginPopup = jest.fn()

jest.mock('@azure/msal-react', () => ({
  useIsAuthenticated: jest.fn(),
  useMsal: jest.fn(),
}))

const mockUseIsAuthenticated = useIsAuthenticated as jest.Mock
const mockUseMsal = useMsal as jest.Mock

beforeEach(() => {
  jest.clearAllMocks()
  mockUseMsal.mockReturnValue({ instance: { loginPopup: mockLoginPopup } })
})

describe('AuthGate', () => {
  it('renders SignInCard when unauthenticated', () => {
    mockUseIsAuthenticated.mockReturnValue(false)
    render(<AuthGate><div>Protected content</div></AuthGate>)
    expect(screen.getByRole('button', { name: /sign in with microsoft/i })).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    mockUseIsAuthenticated.mockReturnValue(true)
    render(<AuthGate><div>Protected content</div></AuthGate>)
    expect(screen.getByText('Protected content')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /sign in with microsoft/i })).not.toBeInTheDocument()
  })

  it('calls loginPopup with the API scope when sign in button is clicked', async () => {
    const user = userEvent.setup()
    mockUseIsAuthenticated.mockReturnValue(false)
    render(<AuthGate><div>Protected content</div></AuthGate>)
    await user.click(screen.getByRole('button', { name: /sign in with microsoft/i }))
    expect(mockLoginPopup).toHaveBeenCalledWith({
      scopes: [process.env.NEXT_PUBLIC_ENTRA_API_SCOPE],
    })
  })
})
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd apps/frontend && npm test -- --testPathPattern=AuthGate --no-coverage
```

Expected: all 3 tests fail — modules not found.

- [ ] **Step 3: Create `apps/frontend/src/features/auth/msalConfig.ts`**

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

- [ ] **Step 4: Create `apps/frontend/src/features/auth/components/AuthGate.tsx`**

```tsx
'use client'

import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { SignInCard } from './SignInCard'

interface AuthGateProps {
  children: React.ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const isAuthenticated = useIsAuthenticated()
  const { instance } = useMsal()

  const handleSignIn = () => {
    instance.loginPopup({
      scopes: [process.env.NEXT_PUBLIC_ENTRA_API_SCOPE!],
    })
  }

  if (!isAuthenticated) {
    return <SignInCard onSignIn={handleSignIn} />
  }

  return <>{children}</>
}
```

- [ ] **Step 5: Run tests — verify GREEN**

```bash
cd apps/frontend && npm test -- --testPathPattern=AuthGate --no-coverage
```

Expected: all 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/features/auth/msalConfig.ts \
        apps/frontend/src/features/auth/components/AuthGate.tsx \
        apps/frontend/src/__tests__/AuthGate.test.tsx
git commit -m "feat(frontend): add AuthGate component and MSAL config (FE-07)"
```

---

## Task 5: useToken hook (TDD)

**Files:**
- Create: `apps/frontend/src/__tests__/useToken.test.ts`
- Create: `apps/frontend/src/features/auth/hooks/useToken.ts`

- [ ] **Step 1: Create test file**

Create `apps/frontend/src/__tests__/useToken.test.ts`:

```ts
import { renderHook } from '@testing-library/react'
import { useToken } from '@/features/auth/hooks/useToken'
import { useMsal } from '@azure/msal-react'

jest.mock('@azure/msal-react', () => ({
  useMsal: jest.fn(),
}))

jest.mock('@azure/msal-browser', () => ({
  InteractionRequiredAuthError: class InteractionRequiredAuthError extends Error {
    constructor(errorCode: string) {
      super(errorCode)
      this.name = 'InteractionRequiredAuthError'
    }
  },
}))

const mockUseMsal = useMsal as jest.Mock

beforeEach(() => {
  jest.clearAllMocks()
})

describe('useToken', () => {
  it('returns the access token from acquireTokenSilent on success', async () => {
    mockUseMsal.mockReturnValue({
      instance: {
        acquireTokenSilent: jest.fn().mockResolvedValue({ accessToken: 'silent-token' }),
        acquireTokenPopup: jest.fn(),
      },
      accounts: [{ username: 'user@example.com' }],
    })

    const { result } = renderHook(() => useToken())
    const token = await result.current.getToken()
    expect(token).toBe('silent-token')
  })

  it('falls back to acquireTokenPopup when silent throws InteractionRequiredAuthError', async () => {
    const { InteractionRequiredAuthError: MockError } = jest.requireMock('@azure/msal-browser')
    mockUseMsal.mockReturnValue({
      instance: {
        acquireTokenSilent: jest.fn().mockRejectedValue(new MockError('interaction_required')),
        acquireTokenPopup: jest.fn().mockResolvedValue({ accessToken: 'popup-token' }),
      },
      accounts: [{ username: 'user@example.com' }],
    })

    const { result } = renderHook(() => useToken())
    const token = await result.current.getToken()
    expect(token).toBe('popup-token')
  })
})
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd apps/frontend && npm test -- --testPathPattern=useToken --no-coverage
```

Expected: both tests fail — module not found.

- [ ] **Step 3: Create `apps/frontend/src/features/auth/hooks/useToken.ts`**

```ts
'use client'

import { InteractionRequiredAuthError } from '@azure/msal-browser'
import { useMsal } from '@azure/msal-react'

export function useToken() {
  const { instance, accounts } = useMsal()
  const scope = process.env.NEXT_PUBLIC_ENTRA_API_SCOPE!

  const getToken = async (): Promise<string> => {
    try {
      const response = await instance.acquireTokenSilent({
        scopes: [scope],
        account: accounts[0],
      })
      return response.accessToken
    } catch (err) {
      if (err instanceof InteractionRequiredAuthError) {
        const response = await instance.acquireTokenPopup({ scopes: [scope] })
        return response.accessToken
      }
      throw err
    }
  }

  return { getToken }
}
```

- [ ] **Step 4: Run tests — verify GREEN**

```bash
cd apps/frontend && npm test -- --testPathPattern=useToken --no-coverage
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/features/auth/hooks/useToken.ts \
        apps/frontend/src/__tests__/useToken.test.ts
git commit -m "feat(frontend): add useToken hook with silent→popup fallback (FE-07)"
```

---

## Task 6: Wire Providers, layout, page — integration

**Files:**
- Create: `apps/frontend/src/app/Providers.tsx`
- Modify: `apps/frontend/src/app/layout.tsx`
- Modify: `apps/frontend/src/app/page.tsx`
- Modify: `apps/frontend/src/__tests__/page.test.tsx`

> `layout.tsx` stays a **Server Component** to preserve the `metadata` export. `MsalProvider` requires a Client Component, so it lives in a new `Providers.tsx` wrapper — the standard Next.js App Router pattern.

- [ ] **Step 1: Add MSAL mock to `apps/frontend/src/__tests__/page.test.tsx`**

`page.tsx` now renders `<AuthGate>` which imports from `@azure/msal-react`. Add this mock at the top of the file, right after the existing `jest.mock('@/features/chat/api/streamMessage', ...)` call:

```ts
jest.mock('@azure/msal-react', () => ({
  useIsAuthenticated: jest.fn().mockReturnValue(true),
  useMsal: jest.fn().mockReturnValue({ instance: { loginPopup: jest.fn() } }),
}))
```

- [ ] **Step 2: Run page tests — verify they still pass (before wiring)**

```bash
cd apps/frontend && npm test -- --testPathPattern=page --no-coverage
```

Expected: all 5 existing page tests pass (MSAL mock added, page not yet changed).

- [ ] **Step 3: Create `apps/frontend/src/app/Providers.tsx`**

```tsx
'use client'

import { MsalProvider } from '@azure/msal-react'
import { msalInstance } from '@/features/auth/msalConfig'

export function Providers({ children }: { children: React.ReactNode }) {
  return <MsalProvider instance={msalInstance}>{children}</MsalProvider>
}
```

- [ ] **Step 4: Update `apps/frontend/src/app/layout.tsx`**

Replace the full file:

```tsx
import type { Metadata } from 'next'
import { Geist } from 'next/font/google'
import './globals.css'
import { Providers } from './Providers'

const geist = Geist({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Group One RTP — AI Assistant',
  description: 'Ask questions about your SharePoint list in plain English.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={geist.className} suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

- [ ] **Step 5: Update `apps/frontend/src/app/page.tsx`**

Add the `AuthGate` import and wrap the entire `HomePage` function body. Replace the full file:

```tsx
'use client'

import { useState } from 'react'
import { Sparkles, AlertTriangle, AlignLeft, User, Clock } from 'lucide-react'

import { ChatHeader } from '@/features/chat/components/ChatHeader'
import { ChatInput } from '@/features/chat/components/ChatInput'
import { ChatThread } from '@/features/chat/components/ChatThread'
import { useChat } from '@/features/chat/hooks/useChat'
import { AuthGate } from '@/features/auth/components/AuthGate'

const SUGGESTIONS = [
  { label: 'Show overdue tasks',        icon: AlertTriangle, tint: 'var(--status-red)' },
  { label: 'Summarize the list',        icon: AlignLeft,     tint: 'var(--brand)' },
  { label: 'Who has the most tasks?',   icon: User,          tint: 'var(--status-green)' },
  { label: 'High-priority in progress', icon: Clock,         tint: 'var(--status-amber)' },
]

export default function HomePage() {
  const { messages, streamingText, isStreaming, streamError, sendMessage, stopStream, resetSession } = useChat()

  return (
    <AuthGate>
      {messages.length > 0 ? (
        <div style={{ height: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--background)', overflow: 'hidden' }}>
          <ChatHeader onNewConversation={resetSession} />
          <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }} className="scroll">
            <ChatThread
              messages={messages}
              streamingText={streamingText}
              isStreaming={isStreaming}
              streamError={streamError}
            />
          </div>
          <div style={{
            flexShrink: 0,
            borderTop: '1px solid var(--border)',
            background: 'rgba(255,255,255,.9)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
          }}>
            <div style={{ maxWidth: 780, margin: '0 auto', padding: '14px 24px 16px' }}>
              <ChatInput onSubmit={sendMessage} onStop={stopStream} isStreaming={isStreaming} compact />
            </div>
          </div>
        </div>
      ) : (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
          <ChatHeader />
          <div style={{
            flex: 1, overflowY: 'auto',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            padding: '40px 24px',
          }}>
            <div style={{ width: '100%', maxWidth: 680 }}>
              <div style={{ textAlign: 'center', marginBottom: 26 }}>
                <div style={{
                  width: 52, height: 52, borderRadius: 14,
                  background: 'var(--brand)', color: '#fff',
                  margin: '0 auto 18px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: 'var(--shadow-card-md)',
                }}>
                  <Sparkles style={{ width: 26, height: 26 }} strokeWidth={2.1} />
                </div>
                <h1 style={{ fontSize: 30, fontWeight: 680, letterSpacing: '-.025em', margin: '0 0 8px' }}>
                  SharePoint List AI Assistant
                </h1>
                <p style={{ fontSize: 15.5, color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.5 }}>
                  Ask anything about{' '}
                  <span style={{ fontWeight: 550, color: 'var(--foreground)' }}>Project Tasks</span>
                  {' '}in plain English — no formulas, no filters.
                </p>
              </div>

              <ChatInput onSubmit={sendMessage} onStop={stopStream} isStreaming={isStreaming} />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 18 }}>
                {SUGGESTIONS.map(s => <SuggestionCard key={s.label} {...s} onSubmit={sendMessage} />)}
              </div>
            </div>
          </div>
        </div>
      )}
    </AuthGate>
  )
}

function SuggestionCard({
  label, icon: Icon, tint, onSubmit,
}: {
  label: string
  icon: React.ElementType
  tint: string
  onSubmit: (text: string) => void
}) {
  const [hovered, setHovered] = useState(false)
  return (
    <button
      onClick={() => onSubmit(label)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: 11,
        padding: '13px 15px', textAlign: 'left',
        background: 'var(--card)',
        border: `1px solid ${hovered ? 'var(--border-strong)' : 'var(--border)'}`,
        borderRadius: 11, cursor: 'pointer', fontFamily: 'inherit',
        boxShadow: hovered ? 'var(--shadow-card-md)' : 'var(--shadow-card-sm)',
        transform: hovered ? 'translateY(-1px)' : 'none',
        transition: 'all .16s',
      }}
    >
      <span style={{
        width: 30, height: 30, borderRadius: 8, flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--muted-2)', border: '1px solid var(--border)',
        color: tint,
      }}>
        <Icon style={{ width: 15, height: 15 }} />
      </span>
      <span style={{ fontSize: 13.5, fontWeight: 500, color: 'var(--foreground)' }}>{label}</span>
    </button>
  )
}
```

- [ ] **Step 6: Run full test suite — verify GREEN**

```bash
cd apps/frontend && npm test -- --no-coverage
```

Expected: all 52 tests pass across 10 suites (44 existing + 3 SignInCard + 3 AuthGate + 2 useToken).

- [ ] **Step 7: Commit**

```bash
git add apps/frontend/src/app/Providers.tsx \
        apps/frontend/src/app/layout.tsx \
        apps/frontend/src/app/page.tsx \
        apps/frontend/src/__tests__/page.test.tsx
git commit -m "feat(frontend): wire MsalProvider and AuthGate into app shell (FE-07)"
```

---

## Task 7: Create .env.local.example

**Files:**
- Create: `apps/frontend/.env.local.example`

- [ ] **Step 1: Create the example env file**

Create `apps/frontend/.env.local.example` with this exact content:

```
# Entra ID app registration — public values, safe to commit
NEXT_PUBLIC_ENTRA_CLIENT_ID=
NEXT_PUBLIC_ENTRA_TENANT_ID=

# API scope exposed by your Entra app registration
# Format: api://<client-id>/access_as_user
NEXT_PUBLIC_ENTRA_API_SCOPE=
```

- [ ] **Step 2: Verify .env.local is gitignored**

```bash
grep -n "\.env\.local" apps/frontend/.gitignore 2>/dev/null || grep -n "\.env\.local" .gitignore 2>/dev/null || echo "check root .gitignore"
```

If `.env.local` is not already ignored, add it:
```bash
echo ".env.local" >> apps/frontend/.gitignore
```

- [ ] **Step 3: Commit**

```bash
git add apps/frontend/.env.local.example
git commit -m "chore(frontend): add .env.local.example for Entra config (FE-07)"
```

---

## Task 8: Update Obsidian story board

- [ ] **Step 1: Mark FE-07 as done**

```bash
obsidian vault="Group One RTP" property:set name="tag" value="done" file="FE-07 Entra Sign-in and Auth Gate"
```

- [ ] **Step 2: Update the Story Board**

```bash
obsidian vault="Group One RTP" read file="Story Board - Frontend"
```

Update the FE-07 row status from `` `todo` `` to `` `done` ``.

- [ ] **Step 3: Add daily note entry**

```bash
obsidian vault="Group One RTP" daily:append content="- Completed FE-07 Entra Sign-in and Auth Gate: MsalProvider in Providers.tsx, AuthGate with SignInCard, useToken hook with silent→popup fallback, full auth gate wired into page.tsx"
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: mark FE-07 done in story board (FE-07)"
```
