# FE-05 — Session Conversation History: Design Spec

**Date:** 2026-06-05
**Story:** FE-05 Session Conversation History
**Status:** Approved

---

## Overview

Retain conversation history for the duration of the browser session and send a stable session identifier with each request so the backend can maintain server-side chat history for follow-up context.

---

## Architecture & Data Flow

No new files. All changes are confined to two existing files in the `chat` feature slice:

```
features/chat/
  api/streamMessage.ts   — add sessionId param to signature (stub ignores it)
  hooks/useChat.ts       — generate sessionId via useRef, pass to streamMessage,
                           expose resetSession
```

**Data flow:**

1. `useChat` initialises `sessionIdRef` once with `crypto.randomUUID()` as the `useRef` initial value.
2. Every `sendMessage(text)` call passes `(text, sessionIdRef.current, signal)` to `streamMessage`.
3. `streamMessage` stub accepts `sessionId` but ignores it — FE-08 will use it for the real POST.
4. `resetSession()` clears `messages`, `streamingText`, `streamError`, `isStreaming`, and assigns a fresh UUID to `sessionIdRef.current`.

Conversation history (the `messages` array) persists as long as `useChat` stays mounted. Clearing it requires an explicit `resetSession()` call, which FE-06 will wire to the "New Conversation" control.

---

## Component Changes

### `streamMessage.ts`

Add `sessionId: string` as the second parameter, before `signal`. Stub body is unchanged.

```ts
export async function* streamMessage(
  text: string,
  sessionId: string,   // stub ignores; FE-08 will POST with it
  signal: AbortSignal
): AsyncGenerator<string>
```

### `useChat.ts`

Three additions:

1. `const sessionIdRef = useRef<string>(crypto.randomUUID())` — initialised once, never triggers re-renders.
2. `sendMessage` passes `sessionIdRef.current` as the second argument to `streamMessage`.
3. New `resetSession` callback resets all state fields (`messages`, `streamingText`, `streamError`, `isStreaming`) and rotates `sessionIdRef.current` to a new `crypto.randomUUID()`.

**Updated return shape:**

```ts
return {
  messages,
  streamingText,
  isStreaming,
  streamError,
  sendMessage,
  stopStream,
  resetSession,   // ← new
}
```

No changes to `types.ts` or any consumer components — `resetSession` is additive.

---

## Testing

### `streamMessage.test.ts`

Update all existing calls to pass a dummy `sessionId` string (e.g. `'test-session'`) — interface change only, no behaviour change.

### `useChat.test.ts` — additions

| Test | Description |
|---|---|
| Session ID generated on mount | `sessionId` passed to `streamMessage` is a valid UUID (matches `/^[0-9a-f-]{36}$/`) |
| Session ID is stable within a session | Same ID passed on consecutive `sendMessage` calls |
| `resetSession` clears messages | `messages` is `[]` after reset |
| `resetSession` clears streaming state | `streamingText`, `streamError`, `isStreaming` all reset |
| `resetSession` rotates session ID | ID after reset differs from ID before reset |
| `sendMessage` after reset uses new ID | New ID is passed to `streamMessage` after `resetSession` |

All additions go into existing test files — no new files.

---

## Constraints

- **No persistent storage** — `sessionStorage`, `localStorage`, cookies are out of scope for v1 (Architecture §5.4).
- **No URL / querystring exposure** of the session ID.
- Session ID is opaque to the UI; it is never rendered.
- `crypto.randomUUID()` is used for ID generation — available in all supported browsers (Chromium, Firefox, Safari 15.4+).
