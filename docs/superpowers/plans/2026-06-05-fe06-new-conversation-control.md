# FE-06 New Conversation Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "New conversation" button to the chat header that immediately clears the thread and resets the session.

**Architecture:** `ChatHeader` gains an optional `onNewConversation` prop; when provided it renders a shadcn ghost Button in the header's right side. `page.tsx` passes `resetSession` (from `useChat`) as that prop only in the conversation view — absent on the landing/empty state.

**Tech Stack:** React, Next.js App Router, shadcn/ui Button, lucide-react Plus icon, Jest + Testing Library.

---

## File Map

| File | Change |
|---|---|
| `apps/frontend/src/features/chat/components/ChatHeader.tsx` | Add `onNewConversation?` prop + conditional Button |
| `apps/frontend/src/app/page.tsx` | Destructure `resetSession`, pass to ChatHeader in conversation branch |
| `apps/frontend/src/__tests__/ChatHeader.test.tsx` | New — 3 unit tests for the button |
| `apps/frontend/src/__tests__/page.test.tsx` | Add 1 integration test for new-conversation flow |

---

## Task 1: Create and checkout feature branch

- [ ] **Step 1: Create and switch to the feature branch**

```bash
git checkout -b feature/FE-06-new-conversation
```

Expected: `Switched to a new branch 'feature/FE-06-new-conversation'`

---

## Task 2: ChatHeader — tests first

**Files:**
- Create: `apps/frontend/src/__tests__/ChatHeader.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `apps/frontend/src/__tests__/ChatHeader.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatHeader } from '@/features/chat/components/ChatHeader'

describe('ChatHeader', () => {
  it('does not render a new conversation button when onNewConversation is not provided', () => {
    render(<ChatHeader />)
    expect(screen.queryByRole('button', { name: /new conversation/i })).not.toBeInTheDocument()
  })

  it('renders a new conversation button when onNewConversation is provided', () => {
    render(<ChatHeader onNewConversation={() => {}} />)
    expect(screen.getByRole('button', { name: /new conversation/i })).toBeInTheDocument()
  })

  it('calls onNewConversation when the button is clicked', async () => {
    const user = userEvent.setup()
    const onNewConversation = jest.fn()
    render(<ChatHeader onNewConversation={onNewConversation} />)
    await user.click(screen.getByRole('button', { name: /new conversation/i }))
    expect(onNewConversation).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd apps/frontend && npm test -- --testPathPattern=ChatHeader --no-coverage
```

Expected: all 3 tests fail — `ChatHeader` doesn't accept props yet.

---

## Task 3: Implement ChatHeader button

**Files:**
- Modify: `apps/frontend/src/features/chat/components/ChatHeader.tsx`

- [ ] **Step 1: Replace the full file content with the updated component**

```tsx
import { Plus, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatHeaderProps {
  onNewConversation?: () => void
}

export function ChatHeader({ onNewConversation }: ChatHeaderProps) {
  return (
    <header style={{
      height: 56, flexShrink: 0,
      borderBottom: '1px solid var(--border)',
      background: 'rgba(255,255,255,.82)',
      backdropFilter: 'blur(10px) saturate(1.1)',
      WebkitBackdropFilter: 'blur(10px) saturate(1.1)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 20px', position: 'sticky', top: 0, zIndex: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
        <div style={{
          width: 30, height: 30, borderRadius: 8,
          background: 'var(--brand)', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: 'var(--shadow-card-sm)',
        }}>
          <Sparkles style={{ width: 17, height: 17 }} strokeWidth={2.2} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
          <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-.01em' }}>List AI Assistant</span>
          <span style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>SharePoint · Group.one</span>
        </div>
      </div>
      {onNewConversation && (
        <Button variant="ghost" size="sm" onClick={onNewConversation}>
          <Plus className="h-4 w-4" />
          New conversation
        </Button>
      )}
    </header>
  )
}
```

Key changes from the original:
- Added `justifyContent: 'space-between'` to the header's flex container so the button sits on the right
- Wrapped logo/title in a `<div>` (left group)
- Added `Button` import from `@/components/ui/button` and `Plus` from `lucide-react`
- Conditional button on the right when `onNewConversation` is provided

- [ ] **Step 2: Run tests — verify GREEN**

```bash
cd apps/frontend && npm test -- --testPathPattern=ChatHeader --no-coverage
```

Expected: all 3 tests pass.

- [ ] **Step 3: Commit**

```bash
git add apps/frontend/src/features/chat/components/ChatHeader.tsx \
        apps/frontend/src/__tests__/ChatHeader.test.tsx
git commit -m "feat(frontend): add new conversation button to ChatHeader (FE-06)"
```

---

## Task 4: Wire page.tsx — integration test first

**Files:**
- Modify: `apps/frontend/src/__tests__/page.test.tsx`
- Modify: `apps/frontend/src/app/page.tsx`

- [ ] **Step 1: Add the integration test to `apps/frontend/src/__tests__/page.test.tsx`**

The existing mock at the top of the file is:

```ts
jest.mock('@/features/chat/api/streamMessage', () => ({
  streamMessage: jest.fn().mockImplementation(async function* () {
    yield 'Streamed response'
  }),
}))
```

Append this test inside the existing `describe('HomePage', ...)` block, after the last existing test:

```ts
  it('shows new conversation button after a message is sent and clicking it returns to empty state', async () => {
    const user = userEvent.setup()
    render(<HomePage />)

    // Send a message to enter conversation view
    await user.type(screen.getByPlaceholderText(/ask a question/i), 'Hello')
    await user.keyboard('{Enter}')
    await waitFor(() => expect(screen.getByText('Streamed response')).toBeInTheDocument())

    // New conversation button should now be visible
    const newConvButton = screen.getByRole('button', { name: /new conversation/i })
    expect(newConvButton).toBeInTheDocument()

    // Click it — thread clears, landing heading returns
    await user.click(newConvButton)
    expect(screen.getByText('SharePoint List AI Assistant')).toBeInTheDocument()
    expect(screen.queryByText('Hello')).not.toBeInTheDocument()
  })
```

- [ ] **Step 2: Run test — verify RED**

```bash
cd apps/frontend && npm test -- --testPathPattern=page --no-coverage
```

Expected: the new test fails — `page.tsx` doesn't pass `onNewConversation` to `ChatHeader` yet.

- [ ] **Step 3: Update `apps/frontend/src/app/page.tsx`**

Two changes:
1. Add `resetSession` to the `useChat()` destructure on line 19.
2. Pass `onNewConversation={resetSession}` to the `<ChatHeader />` in the `messages.length > 0` branch (first return).

Replace the full file:

```tsx
'use client'

import { useState } from 'react'
import { Sparkles, AlertTriangle, AlignLeft, User, Clock } from 'lucide-react'

import { ChatHeader } from '@/features/chat/components/ChatHeader'
import { ChatInput } from '@/features/chat/components/ChatInput'
import { ChatThread } from '@/features/chat/components/ChatThread'
import { useChat } from '@/features/chat/hooks/useChat'

const SUGGESTIONS = [
  { label: 'Show overdue tasks',        icon: AlertTriangle, tint: 'var(--status-red)' },
  { label: 'Summarize the list',        icon: AlignLeft,     tint: 'var(--brand)' },
  { label: 'Who has the most tasks?',   icon: User,          tint: 'var(--status-green)' },
  { label: 'High-priority in progress', icon: Clock,         tint: 'var(--status-amber)' },
]

export default function HomePage() {
  const { messages, streamingText, isStreaming, streamError, sendMessage, stopStream, resetSession } = useChat()

  if (messages.length > 0) {
    return (
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
    )
  }

  return (
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

- [ ] **Step 4: Run page tests — verify GREEN**

```bash
cd apps/frontend && npm test -- --testPathPattern=page --no-coverage
```

Expected: all 5 page tests pass (4 existing + 1 new).

- [ ] **Step 5: Run full suite — verify no regressions**

```bash
cd apps/frontend && npm test -- --no-coverage
```

Expected: all tests pass (43 total across all suites).

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/app/page.tsx \
        apps/frontend/src/__tests__/page.test.tsx
git commit -m "feat(frontend): wire resetSession to ChatHeader new conversation button (FE-06)"
```

---

## Task 5: Update Obsidian story board

- [ ] **Step 1: Mark FE-06 as done**

```bash
obsidian vault="Group One RTP" property:set name="tag" value="done" file="FE-06 New Conversation Control"
```

- [ ] **Step 2: Update the Story Board**

Read the story board first:

```bash
obsidian vault="Group One RTP" read file="Story Board - Frontend"
```

Then update the FE-06 row status from `` `todo` `` to `` `done` ``.

- [ ] **Step 3: Add daily note entry**

```bash
obsidian vault="Group One RTP" daily:append content="- Completed FE-06 New Conversation Control: ghost Button in ChatHeader with onNewConversation prop, wired to resetSession in page.tsx conversation branch only"
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: mark FE-06 done in story board (FE-06)"
```
