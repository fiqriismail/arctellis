# FE-04 SSE Streaming & Loading Indicator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the synchronous `STUB_RESPONSE` in `page.tsx` with token-by-token streaming: a `useChat` hook drives a stub `AsyncGenerator`, `ChatThread` shows bouncing dots while streaming, and `ChatInput`'s send button becomes a stop square during generation.

**Architecture:** A new `streamMessage` async generator in `features/chat/api/` is the swap-point for FE-08. A new `useChat` hook in `features/chat/hooks/` owns all streaming state (`messages`, `streamingText`, `isStreaming`, `streamError`, `AbortController`). `page.tsx` calls the hook and passes props down; `ChatThread` and `ChatInput` receive new optional props and handle the visual changes.

**Tech Stack:** React 19, TypeScript strict, `@testing-library/react` v16 (`renderHook`, `waitFor`, `act`), Jest 30 fake timers, lucide-react `Square` icon.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `apps/frontend/src/features/chat/api/streamMessage.ts` | Create | Stub `AsyncGenerator` — yields tokens with 80 ms delay; FE-08 replaces body |
| `apps/frontend/src/features/chat/hooks/useChat.ts` | Create | All streaming state + `sendMessage` / `stopStream` logic |
| `apps/frontend/src/features/chat/components/ChatThread.tsx` | Modify | Accept `streamingText`, `isStreaming`, `streamError` props; render `TypingIndicator` and inline error |
| `apps/frontend/src/features/chat/components/ChatInput.tsx` | Modify | Accept `isStreaming` / `onStop`; toggle send ↔ stop button |
| `apps/frontend/src/app/page.tsx` | Modify | Replace `STUB_RESPONSE` + `handleSubmit` with `useChat`; pass new props |
| `apps/frontend/src/app/globals.css` | Modify | Add `@keyframes typingBounce` |
| `apps/frontend/src/__tests__/streamMessage.test.ts` | Create | 3 tests for the stub generator |
| `apps/frontend/src/__tests__/useChat.test.ts` | Create | 5 tests for the hook (mocks `streamMessage`) |
| `apps/frontend/src/__tests__/ChatThread.test.tsx` | Modify | Add 2 new streaming tests; existing 5 pass unchanged (new props are optional) |
| `apps/frontend/src/__tests__/ChatInput.test.tsx` | Create | 2 tests for send/stop button toggle |
| `apps/frontend/src/__tests__/page.test.tsx` | Modify | Mock `streamMessage`, update 2 assertions to use `waitFor` |

---

## Task 1: `streamMessage` stub

**Files:**
- Create: `apps/frontend/src/features/chat/api/streamMessage.ts`
- Create: `apps/frontend/src/__tests__/streamMessage.test.ts`

### Step 1 — Write the failing tests

- [ ] **Create `apps/frontend/src/__tests__/streamMessage.test.ts`:**

```ts
import { streamMessage } from '@/features/chat/api/streamMessage'

describe('streamMessage', () => {
  beforeEach(() => { jest.useFakeTimers() })
  afterEach(() => { jest.useRealTimers() })

  it('yields tokens that together contain the stub text', async () => {
    const controller = new AbortController()
    const tokens: string[] = []

    const collecting = (async () => {
      for await (const token of streamMessage('any question', controller.signal)) {
        tokens.push(token)
      }
    })()

    await jest.runAllTimersAsync()
    await collecting

    expect(tokens.length).toBeGreaterThan(0)
    expect(tokens.join('')).toContain('FE-08')
  })

  it('throws AbortError and stops after the signal is aborted', async () => {
    const controller = new AbortController()
    const tokens: string[] = []
    let caughtError: Error | null = null

    const collecting = (async () => {
      try {
        for await (const token of streamMessage('test', controller.signal)) {
          tokens.push(token)
          if (tokens.length === 1) controller.abort()
        }
      } catch (err) {
        caughtError = err as Error
      }
    })()

    await jest.runAllTimersAsync()
    await collecting

    expect(tokens.length).toBe(1)
    expect(caughtError).not.toBeNull()
    expect(caughtError?.name).toBe('AbortError')
  })

  it('throws AbortError immediately if signal is already aborted before first token', async () => {
    const controller = new AbortController()
    controller.abort()
    const tokens: string[] = []
    let caughtError: Error | null = null

    try {
      for await (const token of streamMessage('test', controller.signal)) {
        tokens.push(token)
      }
    } catch (err) {
      caughtError = err as Error
    }

    expect(tokens.length).toBe(0)
    expect(caughtError?.name).toBe('AbortError')
  })
})
```

- [ ] **Step 2: Run to confirm 3 failures**

```bash
cd apps/frontend && npx jest streamMessage --no-coverage
```

Expected: 3 failures — "Cannot find module '@/features/chat/api/streamMessage'".

### Step 3 — Implement

- [ ] **Create `apps/frontend/src/features/chat/api/streamMessage.ts`:**

```ts
function delay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException('Aborted', 'AbortError'))
      return
    }
    const id = setTimeout(resolve, ms)
    signal.addEventListener(
      'abort',
      () => { clearTimeout(id); reject(new DOMException('Aborted', 'AbortError')) },
      { once: true }
    )
  })
}

export async function* streamMessage(
  _text: string,
  signal: AbortSignal
): AsyncGenerator<string> {
  const tokens = 'This is a stub response — real answers arrive in FE-08.'.split(' ')
  for (const token of tokens) {
    await delay(80, signal)
    yield token + ' '
  }
}
```

- [ ] **Step 4: Run to confirm 3 pass**

```bash
cd apps/frontend && npx jest streamMessage --no-coverage
```

Expected: `3 passed, 3 total`.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/features/chat/api/streamMessage.ts \
        apps/frontend/src/__tests__/streamMessage.test.ts
git commit -m "feat(frontend): add streamMessage stub AsyncGenerator (FE-04)"
```

---

## Task 2: `useChat` hook

**Files:**
- Create: `apps/frontend/src/features/chat/hooks/useChat.ts`
- Create: `apps/frontend/src/__tests__/useChat.test.ts`

### Step 1 — Write the failing tests

- [ ] **Create `apps/frontend/src/__tests__/useChat.test.ts`:**

```ts
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '@/features/chat/hooks/useChat'
import { streamMessage } from '@/features/chat/api/streamMessage'

jest.mock('@/features/chat/api/streamMessage')
const mockStreamMessage = streamMessage as jest.Mock

async function* makeTokenStream(tokens: string[]): AsyncGenerator<string> {
  for (const token of tokens) {
    yield token
  }
}

beforeEach(() => {
  jest.clearAllMocks()
})

describe('useChat', () => {
  it('appends the user message to messages immediately on sendMessage', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['Hello']))
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test question')
    })

    expect(result.current.messages[0]).toEqual({ role: 'user', text: 'test question' })
  })

  it('accumulates tokens and adds a completed assistant message when stream ends', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['Hello ', 'world']))
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1]).toEqual({ role: 'assistant', text: 'Hello world' })
    expect(result.current.streamingText).toBe('')
    expect(result.current.isStreaming).toBe(false)
  })

  it('preserves partial text in messages and clears streaming when stopStream is called', async () => {
    mockStreamMessage.mockImplementation(async function* (_: string, signal: AbortSignal) {
      yield 'Partial '
      await new Promise<never>((_, reject) =>
        signal.addEventListener('abort', () =>
          reject(new DOMException('Aborted', 'AbortError'))
        )
      )
    })

    const { result } = renderHook(() => useChat())

    act(() => { result.current.sendMessage('hi') })

    await waitFor(() => expect(result.current.streamingText).toBe('Partial '))

    act(() => { result.current.stopStream() })

    await waitFor(() => expect(result.current.isStreaming).toBe(false))

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1]).toEqual({ role: 'assistant', text: 'Partial ' })
    expect(result.current.streamingText).toBe('')
  })

  it('sets streamError and preserves partial text on stream failure', async () => {
    mockStreamMessage.mockImplementation(async function* () {
      yield 'Partial '
      throw new Error('Network error')
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.streamError).toBe('Something went wrong — please try again')
    expect(result.current.messages[1]).toEqual({ role: 'assistant', text: 'Partial ' })
    expect(result.current.isStreaming).toBe(false)
  })

  it('clears streamError at the start of the next sendMessage', async () => {
    mockStreamMessage.mockImplementationOnce(async function* () {
      throw new Error('fail')
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('first')
    })

    expect(result.current.streamError).toBe('Something went wrong — please try again')

    mockStreamMessage.mockImplementationOnce(() => makeTokenStream(['OK']))

    await act(async () => {
      await result.current.sendMessage('second')
    })

    expect(result.current.streamError).toBeNull()
  })
})
```

- [ ] **Step 2: Run to confirm 5 failures**

```bash
cd apps/frontend && npx jest useChat --no-coverage
```

Expected: 5 failures — "Cannot find module '@/features/chat/hooks/useChat'".

### Step 3 — Implement

- [ ] **Create `apps/frontend/src/features/chat/hooks/useChat.ts`:**

```ts
'use client'

import { useState, useRef, useCallback } from 'react'
import { streamMessage } from '@/features/chat/api/streamMessage'
import type { Message } from '@/features/chat/types'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [streamingText, setStreamingText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamError, setStreamError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (text: string) => {
    if (abortRef.current) return

    setMessages(prev => [...prev, { role: 'user', text }])
    setIsStreaming(true)
    setStreamError(null)
    setStreamingText('')

    const controller = new AbortController()
    abortRef.current = controller

    let accumulated = ''

    try {
      for await (const token of streamMessage(text, controller.signal)) {
        accumulated += token
        setStreamingText(accumulated)
      }
      setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        if (accumulated) {
          setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
        }
      } else {
        if (accumulated) {
          setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
        }
        setStreamError('Something went wrong — please try again')
      }
    } finally {
      setStreamingText('')
      setIsStreaming(false)
      abortRef.current = null
    }
  }, [])

  const stopStream = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, streamingText, isStreaming, streamError, sendMessage, stopStream }
}
```

- [ ] **Step 4: Run to confirm 5 pass**

```bash
cd apps/frontend && npx jest useChat --no-coverage
```

Expected: `5 passed, 5 total`.

- [ ] **Step 5: Run full suite to check for regressions**

```bash
cd apps/frontend && npx jest --no-coverage
```

Expected: `streamMessage ×3, useChat ×5` + all prior tests = 26 total passing.

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/features/chat/hooks/useChat.ts \
        apps/frontend/src/__tests__/useChat.test.ts
git commit -m "feat(frontend): add useChat hook with streaming state (FE-04)"
```

---

## Task 3: `ChatThread` streaming UI

**Files:**
- Modify: `apps/frontend/src/features/chat/components/ChatThread.tsx`
- Modify: `apps/frontend/src/app/globals.css`
- Modify: `apps/frontend/src/__tests__/ChatThread.test.tsx`

### Step 1 — Write the 2 new failing tests

- [ ] **Append to `apps/frontend/src/__tests__/ChatThread.test.tsx`:**

```tsx
  it('shows bouncing dots and partial text when isStreaming is true', () => {
    render(
      <ChatThread
        messages={[{ role: 'user', text: 'Hi' }]}
        isStreaming={true}
        streamingText="Partial ans"
      />
    )
    expect(screen.getByTestId('streaming-message')).toBeInTheDocument()
    expect(screen.getByText('Partial ans')).toBeInTheDocument()
    expect(screen.getByTestId('typing-indicator')).toBeInTheDocument()
  })

  it('shows inline error when isStreaming is false and streamError is set', () => {
    render(
      <ChatThread
        messages={[{ role: 'assistant', text: 'Hello' }]}
        isStreaming={false}
        streamError="Something went wrong — please try again"
      />
    )
    expect(screen.getByTestId('stream-error')).toBeInTheDocument()
    expect(screen.getByText('Something went wrong — please try again')).toBeInTheDocument()
    expect(screen.queryByTestId('typing-indicator')).not.toBeInTheDocument()
  })
```

- [ ] **Step 2: Run to confirm 2 new failures (existing 5 still pass)**

```bash
cd apps/frontend && npx jest ChatThread --no-coverage
```

Expected: 5 pass, 2 fail with `TestingLibraryElementError`.

### Step 3 — Add `@keyframes typingBounce` to globals.css

- [ ] **Add after the existing `@keyframes msgIn` block in `apps/frontend/src/app/globals.css`:**

```css
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.8; }
  30% { transform: translateY(-6px); opacity: 1; }
}
```

### Step 4 — Update `ChatThread.tsx`

- [ ] **Replace the full contents of `apps/frontend/src/features/chat/components/ChatThread.tsx`:**

```tsx
'use client'

import { useRef, useEffect } from 'react'
import { Sparkles } from 'lucide-react'
import { Message } from '@/features/chat/types'
import { MarkdownContent } from '@/features/chat/components/MarkdownContent'

interface ChatThreadProps {
  messages: Message[]
  streamingText?: string
  isStreaming?: boolean
  streamError?: string | null
}

export function ChatThread({
  messages,
  streamingText = '',
  isStreaming = false,
  streamError = null,
}: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  return (
    <div style={{ maxWidth: 780, margin: '0 auto', padding: '28px 24px 16px' }}>
      {messages.map((msg, i) =>
        msg.role === 'user'
          ? <UserMessage key={i} text={msg.text} />
          : <AssistantMessage key={i} text={msg.text} />
      )}
      {isStreaming && (
        <div
          data-testid="streaming-message"
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
            {streamingText && <MarkdownContent text={streamingText} />}
            <TypingIndicator />
          </div>
        </div>
      )}
      {!isStreaming && streamError && (
        <p
          data-testid="stream-error"
          style={{
            fontSize: 13,
            color: 'var(--status-red)',
            textAlign: 'center',
            padding: '8px 0 16px',
          }}
        >
          {streamError}
        </p>
      )}
      <div ref={bottomRef} />
    </div>
  )
}

function TypingIndicator() {
  return (
    <div
      data-testid="typing-indicator"
      style={{ display: 'flex', gap: 5, padding: '6px 0 2px' }}
    >
      {[0, 1, 2].map(i => (
        <span
          key={i}
          style={{
            display: 'inline-block',
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: 'var(--brand)',
            animation: `typingBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
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
        <MarkdownContent text={text} />
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Run ChatThread tests to confirm all 7 pass**

```bash
cd apps/frontend && npx jest ChatThread --no-coverage
```

Expected: `7 passed, 7 total`.

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/features/chat/components/ChatThread.tsx \
        apps/frontend/src/app/globals.css \
        apps/frontend/src/__tests__/ChatThread.test.tsx
git commit -m "feat(frontend): add streaming message row and typing indicator to ChatThread (FE-04)"
```

---

## Task 4: `ChatInput` stop button

**Files:**
- Modify: `apps/frontend/src/features/chat/components/ChatInput.tsx`
- Create: `apps/frontend/src/__tests__/ChatInput.test.tsx`

### Step 1 — Write the 2 failing tests

- [ ] **Create `apps/frontend/src/__tests__/ChatInput.test.tsx`:**

```tsx
import { render, screen } from '@testing-library/react'
import { ChatInput } from '@/features/chat/components/ChatInput'

describe('ChatInput', () => {
  it('shows the stop button when isStreaming is true', () => {
    render(<ChatInput onSubmit={jest.fn()} onStop={jest.fn()} isStreaming={true} />)
    expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /send/i })).not.toBeInTheDocument()
  })

  it('shows the send button when isStreaming is false', () => {
    render(<ChatInput onSubmit={jest.fn()} isStreaming={false} />)
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /stop/i })).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run to confirm 2 failures**

```bash
cd apps/frontend && npx jest ChatInput --no-coverage
```

Expected: 2 failures — button has `aria-label="Send"`, not `"Stop"`.

### Step 3 — Update `ChatInput.tsx`

- [ ] **Replace the full contents of `apps/frontend/src/features/chat/components/ChatInput.tsx`:**

```tsx
'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { ArrowUp, Square } from 'lucide-react'

interface ChatInputProps {
  onSubmit: (question: string) => void
  onStop?: () => void
  isStreaming?: boolean
  disabled?: boolean
  compact?: boolean
}

export function ChatInput({
  onSubmit,
  onStop,
  isStreaming = false,
  disabled = false,
  compact = false,
}: ChatInputProps) {
  const [value, setValue] = useState('')
  const [focused, setFocused] = useState(false)
  const ref = useRef<HTMLTextAreaElement>(null)

  const autosize = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }, [])

  useEffect(() => { autosize() }, [value, autosize])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled || isStreaming) return
    onSubmit(trimmed)
    setValue('')
  }

  const handleStop = () => {
    onStop?.()
  }

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit() }
  }

  const canSend = !!value.trim() && !disabled && !isStreaming
  const buttonActive = isStreaming || canSend

  return (
    <div>
      <div
        style={{
          display: 'flex', alignItems: 'flex-end', gap: 10,
          padding: '10px 10px 10px 16px',
          background: 'var(--card)',
          border: `1px solid ${focused ? 'var(--brand)' : 'var(--border-strong)'}`,
          borderRadius: compact ? 14 : 16,
          boxShadow: focused ? '0 0 0 3px rgba(15,108,189,.12)' : 'var(--shadow-card-md)',
          transition: 'box-shadow .2s, border-color .2s',
        }}
        onFocusCapture={() => setFocused(true)}
        onBlurCapture={() => setFocused(false)}
      >
        <textarea
          ref={ref}
          value={value}
          rows={1}
          disabled={disabled}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask a question about your SharePoint list…"
          style={{
            flex: 1, border: 'none', outline: 'none', resize: 'none',
            background: 'transparent', fontFamily: 'inherit',
            fontSize: 15, lineHeight: 1.5, color: 'var(--foreground)',
            maxHeight: 200, padding: '6px 0', margin: 0,
          }}
        />
        <button
          onClick={isStreaming ? handleStop : handleSubmit}
          disabled={!buttonActive}
          aria-label={isStreaming ? 'Stop' : 'Send'}
          style={{
            width: 34, height: 34, flexShrink: 0, borderRadius: 9,
            border: 'none', cursor: buttonActive ? 'pointer' : 'default',
            background: buttonActive ? 'var(--brand)' : '#e4e4e7', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background .15s', marginBottom: 1,
          }}
        >
          {isStreaming ? (
            <Square style={{ width: 14, height: 14 }} fill="currentColor" strokeWidth={0} />
          ) : (
            <ArrowUp style={{ width: 17, height: 17 }} strokeWidth={2.4} />
          )}
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 10, fontSize: 12, color: '#a1a1aa' }}>
        <span><Kbd>Enter</Kbd> to send</span>
        <span style={{ opacity: .5 }}>·</span>
        <span><Kbd>Shift</Kbd>+<Kbd>Enter</Kbd> for a new line</span>
      </div>
    </div>
  )
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd style={{
      fontFamily: 'ui-monospace, "SF Mono", monospace',
      fontSize: 11, padding: '1.5px 5px', borderRadius: 5,
      background: 'var(--muted)', border: '1px solid var(--border)',
      color: 'var(--muted-foreground)', boxShadow: '0 1px 0 var(--border)',
    }}>{children}</kbd>
  )
}
```

- [ ] **Step 4: Run ChatInput tests to confirm both pass**

```bash
cd apps/frontend && npx jest ChatInput --no-coverage
```

Expected: `2 passed, 2 total`.

- [ ] **Step 5: Run full suite**

```bash
cd apps/frontend && npx jest --no-coverage
```

Expected: `streamMessage ×3, useChat ×5, ChatThread ×7, ChatInput ×2, MarkdownContent ×9, HomePage ×4` = 30 total.

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/features/chat/components/ChatInput.tsx \
        apps/frontend/src/__tests__/ChatInput.test.tsx
git commit -m "feat(frontend): add stop button to ChatInput for streaming (FE-04)"
```

---

## Task 5: Wire `page.tsx`

**Files:**
- Modify: `apps/frontend/src/app/page.tsx`
- Modify: `apps/frontend/src/__tests__/page.test.tsx`

### Step 1 — Update `page.test.tsx` first (tests will fail until page.tsx is wired)

- [ ] **Replace the full contents of `apps/frontend/src/__tests__/page.test.tsx`:**

```tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import HomePage from '@/app/page'

jest.mock('@/features/chat/api/streamMessage', () => ({
  streamMessage: jest.fn().mockImplementation(async function* () {
    yield 'Streamed response'
  }),
}))

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

  it('shows assistant response after submit', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    await user.type(screen.getByPlaceholderText(/ask a question/i), 'Hello')
    await user.keyboard('{Enter}')
    await waitFor(() => expect(screen.getByText('Streamed response')).toBeInTheDocument())
  })

  it('clicking a suggestion card submits it as a user message and shows response', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    await user.click(screen.getByText('Show overdue tasks'))
    expect(screen.getByText('Show overdue tasks')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Streamed response')).toBeInTheDocument())
  })
})
```

- [ ] **Step 2: Run to confirm 2–4 failures (the streaming-related ones)**

```bash
cd apps/frontend && npx jest page --no-coverage
```

Expected: some failures referencing the old `STUB_RESPONSE` text or async behaviour.

### Step 3 — Update `page.tsx`

- [ ] **Replace the full contents of `apps/frontend/src/app/page.tsx`:**

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
  const { messages, streamingText, isStreaming, streamError, sendMessage, stopStream } = useChat()

  if (messages.length > 0) {
    return (
      <div style={{ height: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--background)', overflow: 'hidden' }}>
        <ChatHeader />
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

- [ ] **Step 4: Run the full test suite**

```bash
cd apps/frontend && npx jest --no-coverage
```

Expected: `streamMessage ×3, useChat ×5, ChatThread ×7, ChatInput ×2, MarkdownContent ×9, HomePage ×4` = **30 passed, 30 total**.

- [ ] **Step 5: TypeScript check**

```bash
cd apps/frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/app/page.tsx \
        apps/frontend/src/__tests__/page.test.tsx
git commit -m "feat(frontend): wire useChat into page, replace STUB_RESPONSE with streaming (FE-04)"
```

---

## Self-check: TypeScript

```bash
cd apps/frontend && npx tsc --noEmit
```

Expected: no errors across all changed files.
