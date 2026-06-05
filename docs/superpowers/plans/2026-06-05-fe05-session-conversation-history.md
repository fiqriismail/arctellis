# FE-05 Session Conversation History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a stable per-session UUID in `useChat`, pass it to `streamMessage` on every request, and expose `resetSession` to clear history and rotate the ID.

**Architecture:** `sessionIdRef` lives in `useChat` via `useRef` — stable, never triggers re-renders. `streamMessage`'s signature gains `sessionId` as its second parameter (stub ignores it; FE-08 will POST it). `resetSession` clears all state fields and rotates the ref to a fresh UUID.

**Tech Stack:** React (`useRef`, `useCallback`), `crypto.randomUUID()`, Jest / Testing Library.

---

## File Map

| File | Change |
|---|---|
| `apps/frontend/src/features/chat/api/streamMessage.ts` | Add `sessionId: string` as 2nd param |
| `apps/frontend/src/features/chat/hooks/useChat.ts` | Add `sessionIdRef`, pass to `streamMessage`, add `resetSession` |
| `apps/frontend/src/__tests__/streamMessage.test.ts` | Update 3 call sites for new signature |
| `apps/frontend/src/__tests__/useChat.test.ts` | Fix `stopStream` mock + add 6 new session tests |

---

## Task 1: Create and checkout feature branch

- [ ] **Step 1: Create and switch to the feature branch**

```bash
git checkout -b feature/FE-05-session-history
```

Expected: `Switched to a new branch 'feature/FE-05-session-history'`

---

## Task 2: Update `streamMessage` signature — test first

**Files:**
- Modify: `apps/frontend/src/__tests__/streamMessage.test.ts`
- Modify: `apps/frontend/src/features/chat/api/streamMessage.ts`

The stub currently has two parameters `(_text, signal)`. Adding `sessionId` as the second argument shifts `signal` to position three. The two abort tests rely on the signal — they will fail once the test calls use the new three-argument signature but the implementation has not been updated yet.

- [ ] **Step 1: Update all three call sites in `streamMessage.test.ts`**

In `apps/frontend/src/__tests__/streamMessage.test.ts`, add `'test-session'` as the second argument in all three `streamMessage(...)` calls:

```ts
// Test 1 — line 12
for await (const token of streamMessage('any question', 'test-session', controller.signal)) {

// Test 2 — line 31
for await (const token of streamMessage('test', 'test-session', controller.signal)) {
  tokens.push(token)
  if (tokens.length === 1) controller.abort()

// Test 3 — line 56
for await (const token of streamMessage('test', 'test-session', controller.signal)) {
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd apps/frontend && npm test -- --testPathPattern=streamMessage --no-coverage
```

Expected: the two abort tests fail (`signal.addEventListener is not a function` or similar) because the old implementation receives `'test-session'` where it expects the `AbortSignal`.

- [ ] **Step 3: Update `streamMessage.ts` signature**

Replace the function signature in `apps/frontend/src/features/chat/api/streamMessage.ts`:

```ts
export async function* streamMessage(
  _text: string,
  _sessionId: string, // stub ignores; FE-08 will POST with it
  signal: AbortSignal
): AsyncGenerator<string> {
```

Leave the function body (`delay`, `tokens`, `for` loop) completely unchanged.

- [ ] **Step 4: Run tests — verify GREEN**

```bash
cd apps/frontend && npm test -- --testPathPattern=streamMessage --no-coverage
```

Expected: all 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/features/chat/api/streamMessage.ts \
        apps/frontend/src/__tests__/streamMessage.test.ts
git commit -m "feat(frontend): add sessionId param to streamMessage signature (FE-05)"
```

---

## Task 3: Add session ID tests to `useChat` — test first

**Files:**
- Modify: `apps/frontend/src/__tests__/useChat.test.ts`

The existing `stopStream` test mock uses `(_: string, signal: AbortSignal)`. When `useChat` starts passing three arguments, `signal` will receive `sessionId` (a string) instead of the `AbortSignal` — the test will break. Fix that mock first, then add the new session tests so all new tests fail for the right reason (missing implementation) rather than a mock mismatch.

- [ ] **Step 1: Fix the `stopStream` mock signature in `useChat.test.ts`**

Find this mock in the `stopStream` test (around line 53):

```ts
mockStreamMessage.mockImplementation(async function* (_: string, signal: AbortSignal) {
```

Replace with:

```ts
mockStreamMessage.mockImplementation(async function* (_text: string, _sessionId: string, signal: AbortSignal) {
```

Leave the rest of that mock body unchanged.

- [ ] **Step 2: Add 5 new session ID tests inside the existing `describe('useChat', ...)` block**

Append these tests after the last existing `it(...)` block (after line 131, before the closing `}`):

```ts
  it('passes a valid UUID as sessionId to streamMessage', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    const sessionId = mockStreamMessage.mock.calls[0][1]
    expect(sessionId).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    )
  })

  it('passes the same sessionId on consecutive sendMessage calls', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => { await result.current.sendMessage('first') })
    await act(async () => { await result.current.sendMessage('second') })

    const firstId = mockStreamMessage.mock.calls[0][1]
    const secondId = mockStreamMessage.mock.calls[1][1]
    expect(firstId).toBe(secondId)
  })

  it('resetSession clears messages and all streaming state', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['Hello']))
    const { result } = renderHook(() => useChat())

    await act(async () => { await result.current.sendMessage('test') })
    expect(result.current.messages).toHaveLength(2)

    act(() => { result.current.resetSession() })

    expect(result.current.messages).toHaveLength(0)
    expect(result.current.streamingText).toBe('')
    expect(result.current.streamError).toBeNull()
    expect(result.current.isStreaming).toBe(false)
  })

  it('resetSession generates a new sessionId', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => { await result.current.sendMessage('before') })
    const idBefore = mockStreamMessage.mock.calls[0][1]

    act(() => { result.current.resetSession() })

    await act(async () => { await result.current.sendMessage('after') })
    const idAfter = mockStreamMessage.mock.calls[1][1]

    expect(idAfter).not.toBe(idBefore)
    expect(idAfter).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    )
  })

  it('sendMessage after resetSession uses the new sessionId', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => { await result.current.sendMessage('before') })
    const idBefore = mockStreamMessage.mock.calls[0][1]

    act(() => { result.current.resetSession() })
    jest.clearAllMocks()
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))

    await act(async () => { await result.current.sendMessage('after') })
    const idAfter = mockStreamMessage.mock.calls[0][1]

    expect(idAfter).not.toBe(idBefore)
  })
```

- [ ] **Step 3: Run tests — verify RED**

```bash
cd apps/frontend && npm test -- --testPathPattern=useChat --no-coverage
```

Expected: the 5 new tests fail (session ID is not passed, `resetSession` is undefined). The existing 6 tests should still pass (the stopStream mock fix is a no-op until useChat starts passing 3 args).

---

## Task 4: Implement session ID in `useChat`

**Files:**
- Modify: `apps/frontend/src/features/chat/hooks/useChat.ts`

- [ ] **Step 1: Add `sessionIdRef` and update `sendMessage` in `useChat.ts`**

Replace the full file content with:

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
  const sessionIdRef = useRef(crypto.randomUUID())

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
      for await (const token of streamMessage(text, sessionIdRef.current, controller.signal)) {
        accumulated += token
        setStreamingText(accumulated)
      }
      if (accumulated) {
        setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
      }
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

  const resetSession = useCallback(() => {
    sessionIdRef.current = crypto.randomUUID()
    setMessages([])
    setStreamingText('')
    setStreamError(null)
    setIsStreaming(false)
  }, [])

  return { messages, streamingText, isStreaming, streamError, sendMessage, stopStream, resetSession }
}
```

- [ ] **Step 2: Run tests — verify GREEN**

```bash
cd apps/frontend && npm test -- --testPathPattern=useChat --no-coverage
```

Expected: all 11 tests pass (6 existing + 5 new).

- [ ] **Step 3: Run the full test suite to catch regressions**

```bash
cd apps/frontend && npm test -- --no-coverage
```

Expected: all tests pass including `streamMessage`, `useChat`, `ChatInput`, `ChatThread`, `MarkdownContent`, and `page` test suites.

- [ ] **Step 4: Commit**

```bash
git add apps/frontend/src/features/chat/hooks/useChat.ts \
        apps/frontend/src/__tests__/useChat.test.ts
git commit -m "feat(frontend): generate sessionId in useChat and thread through streamMessage (FE-05)"
```

---

## Task 5: Update Story Board and Obsidian

- [ ] **Step 1: Mark FE-05 as done in Obsidian**

```bash
obsidian vault="Group One RTP" property:set name="tag" value="done" file="FE-05 Session Conversation History"
```

- [ ] **Step 2: Update Story Board**

Open the Story Board note in Obsidian and change the FE-05 status cell from `` `todo` `` to `` `done` ``:

```bash
obsidian vault="Group One RTP" read file="Story Board - Frontend"
```

Then use the `obsidian` CLI `property:set` or inline edit to update the table row for FE-05 so the status reads `` `done` ``.

- [ ] **Step 3: Add daily note entry**

```bash
obsidian vault="Group One RTP" daily:append content="- Completed FE-05 Session Conversation History: sessionIdRef via useRef(crypto.randomUUID()) in useChat, threaded through streamMessage signature, resetSession clears state and rotates ID"
```

- [ ] **Step 4: Commit story board update**

```bash
git add -A
git commit -m "chore: mark FE-05 done in story board (FE-05)"
```
