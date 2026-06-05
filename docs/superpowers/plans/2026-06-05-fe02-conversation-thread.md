# FE-02 Conversation Thread Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a vertical conversation thread that transitions from the empty state when the first message is submitted, with user bubbles right-aligned and assistant turns left-aligned with a brand avatar.

**Architecture:** `page.tsx` owns `messages: Message[]` state. When the array is empty, the existing empty state renders. Once a message is submitted, the layout switches to a full-height chat view: sticky header → scrollable `ChatThread` → docked `ChatInput`. Suggestion cards wire up to the same `handleSubmit` as the composer. A stub assistant response is appended immediately so the thread is testable without a backend (FE-04 replaces it with SSE).

**Tech Stack:** Next.js 16, React 19, TypeScript strict, Tailwind CSS v4, shadcn/ui, Jest + React Testing Library (installed in Task 1)

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `apps/frontend/src/features/chat/types.ts` | Create | `Message` union type shared across FE-02 → FE-04 |
| `apps/frontend/src/features/chat/components/ChatThread.tsx` | Create | Renders `UserMessage` and `AssistantMessage`; auto-scrolls |
| `apps/frontend/src/app/page.tsx` | Modify | Adds `messages` state, `handleSubmit`, conditional layout |
| `apps/frontend/src/app/globals.css` | Modify | `msgIn` keyframe + custom scrollbar |
| `apps/frontend/jest.config.ts` | Create | Jest config for Next.js |
| `apps/frontend/jest.setup.ts` | Create | `@testing-library/jest-dom` import |
| `apps/frontend/src/__tests__/ChatThread.test.tsx` | Create | Unit tests for thread rendering |
| `apps/frontend/src/__tests__/page.test.tsx` | Create | Integration tests for state transitions |

---

## Task 1: Install and configure Jest + React Testing Library

**Files:**
- Create: `apps/frontend/jest.config.ts`
- Create: `apps/frontend/jest.setup.ts`
- Modify: `apps/frontend/package.json` (devDependencies + test script)

- [ ] **Step 1.1: Install test dependencies**

```bash
cd apps/frontend
npm install -D jest jest-environment-jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @types/jest
```

Expected: packages added to `package.json` devDependencies with no errors.

- [ ] **Step 1.2: Create jest.config.ts**

```ts
import type { Config } from 'jest'
import nextJest from 'next/jest'

const createJestConfig = nextJest({ dir: './' })

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterFramework: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
}

export default createJestConfig(config)
```

- [ ] **Step 1.3: Create jest.setup.ts**

```ts
import '@testing-library/jest-dom'
```

- [ ] **Step 1.4: Add test script to package.json**

In `apps/frontend/package.json`, add to `"scripts"`:
```json
"test": "jest",
"test:watch": "jest --watch"
```

- [ ] **Step 1.5: Smoke-test the setup**

Create `apps/frontend/src/__tests__/smoke.test.ts`:
```ts
it('jest is configured', () => {
  expect(true).toBe(true)
})
```

Run:
```bash
cd apps/frontend && npm test -- --testPathPattern=smoke
```

Expected output:
```
PASS  src/__tests__/smoke.test.ts
  ✓ jest is configured
```

Delete `smoke.test.ts` after confirming it passes.

- [ ] **Step 1.6: Commit**

```bash
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp add apps/frontend/jest.config.ts apps/frontend/jest.setup.ts apps/frontend/package.json apps/frontend/package-lock.json
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp commit -m "chore(frontend): add Jest + React Testing Library (FE-02)"
```

---

## Task 2: Define the Message type

**Files:**
- Create: `apps/frontend/src/features/chat/types.ts`

- [ ] **Step 2.1: Create the type file**

```ts
export type UserMessage      = { role: 'user';      text: string }
export type AssistantMessage = { role: 'assistant'; text: string }
export type Message          = UserMessage | AssistantMessage
```

- [ ] **Step 2.2: Verify TypeScript compiles**

```bash
cd apps/frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 2.3: Commit**

```bash
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp add apps/frontend/src/features/chat/types.ts
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp commit -m "feat(frontend): add Message type (FE-02)"
```

---

## Task 3: Build ChatThread (TDD)

**Files:**
- Create: `apps/frontend/src/features/chat/components/ChatThread.tsx`
- Create: `apps/frontend/src/__tests__/ChatThread.test.tsx`

- [ ] **Step 3.1: Write failing tests**

Create `apps/frontend/src/__tests__/ChatThread.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { ChatThread } from '@/features/chat/components/ChatThread'

describe('ChatThread', () => {
  it('renders a user message', () => {
    render(<ChatThread messages={[{ role: 'user', text: 'Hello' }]} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders an assistant message', () => {
    render(<ChatThread messages={[{ role: 'assistant', text: 'World' }]} />)
    expect(screen.getByText('World')).toBeInTheDocument()
  })

  it('renders messages in order', () => {
    render(<ChatThread messages={[
      { role: 'user', text: 'First' },
      { role: 'assistant', text: 'Second' },
    ]} />)
    const items = screen.getAllByTestId('message')
    expect(items[0]).toHaveTextContent('First')
    expect(items[1]).toHaveTextContent('Second')
  })
})
```

- [ ] **Step 3.2: Run tests to confirm they fail**

```bash
cd apps/frontend && npm test -- --testPathPattern=ChatThread
```

Expected: FAIL — `Cannot find module '@/features/chat/components/ChatThread'`

- [ ] **Step 3.3: Implement ChatThread**

Create `apps/frontend/src/features/chat/components/ChatThread.tsx`:
```tsx
'use client'

import { useRef, useEffect } from 'react'
import { Sparkles } from 'lucide-react'
import { Message } from '@/features/chat/types'

interface ChatThreadProps {
  messages: Message[]
}

export function ChatThread({ messages }: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div style={{ maxWidth: 780, margin: '0 auto', padding: '28px 24px 16px' }}>
      {messages.map((msg, i) =>
        msg.role === 'user'
          ? <UserMessage key={i} text={msg.text} />
          : <AssistantMessage key={i} text={msg.text} />
      )}
      <div ref={bottomRef} />
    </div>
  )
}

function UserMessage({ text }: { text: string }) {
  return (
    <div
      data-testid="message"
      className="anim-msg"
      style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 22 }}
    >
      <div style={{
        maxWidth: '78%',
        background: 'var(--muted)',
        color: 'var(--foreground)',
        padding: '10px 15px',
        borderRadius: '16px 16px 4px 16px',
        fontSize: 14.5,
        lineHeight: 1.5,
        whiteSpace: 'pre-wrap',
        fontWeight: 450,
      }}>
        {text}
      </div>
    </div>
  )
}

function AssistantMessage({ text }: { text: string }) {
  return (
    <div
      data-testid="message"
      className="anim-msg"
      style={{ display: 'flex', gap: 13, marginBottom: 30 }}
    >
      <div style={{
        width: 30, height: 30, borderRadius: 8, flexShrink: 0,
        background: 'var(--brand)', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: 'var(--shadow-card-sm)',
      }}>
        <Sparkles style={{ width: 16, height: 16 }} strokeWidth={2.2} />
      </div>
      <div style={{ flex: 1, minWidth: 0, paddingTop: 3 }}>
        <div style={{
          fontSize: 14.5,
          lineHeight: 1.62,
          color: 'var(--foreground)',
          whiteSpace: 'pre-wrap',
        }}>
          {text}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3.4: Run tests to confirm they pass**

```bash
cd apps/frontend && npm test -- --testPathPattern=ChatThread
```

Expected:
```
PASS  src/__tests__/ChatThread.test.tsx
  ChatThread
    ✓ renders a user message
    ✓ renders an assistant message
    ✓ renders messages in order
```

- [ ] **Step 3.5: Commit**

```bash
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp add apps/frontend/src/features/chat/components/ChatThread.tsx apps/frontend/src/__tests__/ChatThread.test.tsx
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp commit -m "feat(frontend): add ChatThread component (FE-02)"
```

---

## Task 4: Update page.tsx with messages state and conditional layout (TDD)

**Files:**
- Modify: `apps/frontend/src/app/page.tsx`
- Create: `apps/frontend/src/__tests__/page.test.tsx`

- [ ] **Step 4.1: Write failing tests**

Create `apps/frontend/src/__tests__/page.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import HomePage from '@/app/page'

describe('HomePage', () => {
  it('shows empty state by default', () => {
    render(<HomePage />)
    expect(screen.getByText('SharePoint List AI Assistant')).toBeInTheDocument()
  })

  it('hides empty state and shows user message after submit', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    const textarea = screen.getByPlaceholderText(/ask a question/i)
    await user.type(textarea, 'Test question')
    await user.keyboard('{Enter}')
    expect(screen.queryByText('SharePoint List AI Assistant')).not.toBeInTheDocument()
    expect(screen.getByText('Test question')).toBeInTheDocument()
  })

  it('shows stub assistant response after submit', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    await user.type(screen.getByPlaceholderText(/ask a question/i), 'Hello')
    await user.keyboard('{Enter}')
    expect(screen.getByText(/Connected to the backend in FE-08/)).toBeInTheDocument()
  })

  it('clicking a suggestion card submits it as a user message', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    await user.click(screen.getByText('Show overdue tasks'))
    expect(screen.getByText('Show overdue tasks')).toBeInTheDocument()
    expect(screen.getByText(/Connected to the backend in FE-08/)).toBeInTheDocument()
  })
})
```

- [ ] **Step 4.2: Run tests to confirm they fail**

```bash
cd apps/frontend && npm test -- --testPathPattern=page.test
```

Expected: FAIL — tests that submit show the title still visible (no state wiring yet).

- [ ] **Step 4.3: Update page.tsx**

Replace the contents of `apps/frontend/src/app/page.tsx` with:
```tsx
'use client'

import { useState } from 'react'
import { Sparkles, AlertTriangle, AlignLeft, User, Clock } from 'lucide-react'

import { ChatHeader } from '@/features/chat/components/ChatHeader'
import { ChatInput } from '@/features/chat/components/ChatInput'
import { ChatThread } from '@/features/chat/components/ChatThread'
import { Message } from '@/features/chat/types'

const SUGGESTIONS = [
  { label: 'Show overdue tasks',        icon: AlertTriangle, tint: 'var(--status-red)' },
  { label: 'Summarize the list',        icon: AlignLeft,     tint: 'var(--brand)' },
  { label: 'Who has the most tasks?',   icon: User,          tint: 'var(--status-green)' },
  { label: 'High-priority in progress', icon: Clock,         tint: 'var(--status-amber)' },
]

const STUB_RESPONSE = 'Connected to the backend in FE-08 — real answers will appear here.'

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([])

  const handleSubmit = (text: string) => {
    setMessages(prev => [
      ...prev,
      { role: 'user', text },
      { role: 'assistant', text: STUB_RESPONSE },
    ])
  }

  if (messages.length > 0) {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
        <ChatHeader />
        <div style={{ flex: 1, overflowY: 'auto' }} className="scroll">
          <ChatThread messages={messages} />
        </div>
        <div style={{
          flexShrink: 0,
          borderTop: '1px solid var(--border)',
          background: 'rgba(255,255,255,.9)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
        }}>
          <div style={{ maxWidth: 780, margin: '0 auto', padding: '14px 24px 16px' }}>
            <ChatInput onSubmit={handleSubmit} compact />
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

          <ChatInput onSubmit={handleSubmit} />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 18 }}>
            {SUGGESTIONS.map(s => <SuggestionCard key={s.label} {...s} onSubmit={handleSubmit} />)}
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

- [ ] **Step 4.4: Run tests to confirm they pass**

```bash
cd apps/frontend && npm test -- --testPathPattern=page.test
```

Expected:
```
PASS  src/__tests__/page.test.tsx
  HomePage
    ✓ shows empty state by default
    ✓ hides empty state and shows user message after submit
    ✓ shows stub assistant response after submit
    ✓ clicking a suggestion card submits it as a user message
```

- [ ] **Step 4.5: Smoke-test in the browser**

The dev server should already be running on port 3000. Take a screenshot:
```bash
npx playwright screenshot --browser chromium http://localhost:3000 /tmp/fe02-empty.png --wait-for-timeout 1500
```
Confirm: empty state renders correctly.

- [ ] **Step 4.6: Commit**

```bash
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp add apps/frontend/src/app/page.tsx apps/frontend/src/__tests__/page.test.tsx
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp commit -m "feat(frontend): wire messages state and thread layout (FE-02)"
```

---

## Task 5: Add msgIn animation and scrollbar styles to globals.css

**Files:**
- Modify: `apps/frontend/src/app/globals.css`

- [ ] **Step 5.1: Add keyframe and utility class**

Add the following inside `apps/frontend/src/app/globals.css`, before the `@layer base` block:

```css
@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}

/* Always visible — animation is an enhancement only */
.anim-msg { opacity: 1; }
@media (prefers-reduced-motion: no-preference) {
  .anim-msg { animation: msgIn .34s cubic-bezier(.2,.7,.3,1) both; }
}

/* Thread scrollbar */
.scroll::-webkit-scrollbar { width: 10px; }
.scroll::-webkit-scrollbar-thumb {
  background: #e4e4e7;
  border-radius: 99px;
  border: 3px solid #fff;
}
.scroll::-webkit-scrollbar-thumb:hover { background: #d4d4d8; }
```

- [ ] **Step 5.2: Verify in the browser**

```bash
npx playwright screenshot --browser chromium http://localhost:3000 /tmp/fe02-anim-check.png --wait-for-timeout 1500
```

Confirm the empty state still looks correct (animation CSS doesn't break the layout).

- [ ] **Step 5.3: Commit**

```bash
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp add apps/frontend/src/app/globals.css
git -C /Users/fiqriismail/Projects/Arctellis/group-one-rtp commit -m "style(frontend): add msgIn animation and thread scrollbar (FE-02)"
```

---

## Task 6: Visual verification of the full thread

- [ ] **Step 6.1: Screenshot the chat state**

Navigate to the app, submit a message, and capture the result:
```bash
npx playwright screenshot --browser chromium http://localhost:3000 /tmp/fe02-thread.png --wait-for-timeout 2000
```

Verify:
- Empty state is gone
- User message appears right-aligned in a muted bubble
- Assistant stub message appears left-aligned with the brand sparkle avatar
- Docked composer is visible at the bottom
- No layout overflow or broken styles

- [ ] **Step 6.2: Run the full test suite**

```bash
cd apps/frontend && npm test
```

Expected: all tests pass.

- [ ] **Step 6.3: Update Obsidian story board**

```bash
obsidian vault="Group One RTP" property:set name="tag" value="done" file="FE-02 Conversation Thread"
```

Update `Story Board - Frontend.md` to change FE-02 status to `done`.

---

## Self-review checklist (completed inline)

- **Spec coverage:** Message type ✓ · UserMessage/AssistantMessage ✓ · auto-scroll ✓ · empty→chat transition ✓ · suggestion card wiring ✓ · stub response ✓ · msgIn animation ✓ · docked composer ✓
- **Placeholders:** None — all steps have concrete code and commands
- **Type consistency:** `Message` defined in Task 2, imported in Task 3 (`ChatThread`) and Task 4 (`page.tsx`). `handleSubmit(text: string)` consistent across both callers
- **Out-of-scope confirmed:** typing indicator, markdown rendering, New chat button, copy button — none appear in this plan
