# FE-04 — SSE Streaming & Loading Indicator Design

**Date:** 2026-06-05
**Story:** FE-04 SSE Streaming & Loading Indicator
**Status:** Approved

---

## Goal

Replace the synchronous `STUB_RESPONSE` in `page.tsx` with a token-by-token streaming experience: an assistant message that builds in real time, a bouncing-dots indicator while generating, and a stop button that lets the user cancel mid-stream.

---

## Decisions

| Question | Decision |
|---|---|
| Loading indicator style | Three bouncing brand-blue dots below the assistant avatar |
| Error handling (stream failure) | Partial text preserved + subtle inline error note: "Something went wrong — please try again" |
| Stop behaviour | Send button becomes a Stop (square) button while streaming; clicking it cancels the stream, preserves partial text, no error shown |
| Input while streaming | User can type freely while streaming; submit is blocked until stop is clicked |
| Backend API dependency (FE-08) | Stub `AsyncGenerator` now; FE-08 replaces the body, signature stays identical |
| Streaming state home | `useChat` hook — not in `page.tsx` directly |
| Partial markdown during stream | `react-markdown` renders gracefully; incomplete constructs show as plain text until closing delimiter arrives (per FE-03 spec) |

---

## Component & File Structure

```
apps/frontend/src/features/chat/
  api/
    streamMessage.ts        ← NEW: stub AsyncGenerator (replaced by FE-08)
  hooks/
    useChat.ts              ← NEW: all streaming state + logic
  components/
    ChatThread.tsx          ← MODIFY: streamingText + isStreaming + streamError props
    ChatInput.tsx           ← MODIFY: send/stop button toggle
  types.ts                  (no change)

apps/frontend/src/app/
  page.tsx                  ← MODIFY: call useChat, pass props down; remove STUB_RESPONSE
```

### `page.tsx` after changes

```tsx
const { messages, streamingText, isStreaming, streamError, sendMessage, stopStream } = useChat()

return (
  <>
    <ChatThread
      messages={messages}
      streamingText={streamingText}
      isStreaming={isStreaming}
      streamError={streamError}
    />
    <ChatInput onSubmit={sendMessage} onStop={stopStream} isStreaming={isStreaming} />
  </>
)
```

---

## State & Data Flow

### `useChat` hook state

```ts
const [messages, setMessages]          = useState<Message[]>([])
const [streamingText, setStreamingText] = useState('')
const [isStreaming, setIsStreaming]     = useState(false)
const [streamError, setStreamError]    = useState<string | null>(null)
const abortRef                          = useRef<AbortController | null>(null)
```

### `sendMessage(text: string)` flow

1. Append `{ role: 'user', text }` to `messages`
2. Set `isStreaming = true`, clear `streamError`, reset `streamingText = ''`
3. Create fresh `AbortController`, store in `abortRef`
4. Iterate `streamMessage(text, signal)` async generator, concatenating each token onto `streamingText`
5. **Normal completion:** push `{ role: 'assistant', text: streamingText }` into `messages`, clear `streamingText`, set `isStreaming = false`
6. **`AbortError` (user clicked stop):** if `streamingText` is non-empty, push `{ role: 'assistant', text: streamingText }` into `messages`; clear `streamingText`, set `isStreaming = false` — no error shown. If no tokens arrived yet, nothing is pushed.
7. **Any other error:** if `streamingText` is non-empty, push partial text into `messages`; set `streamError = 'Something went wrong — please try again'`, set `isStreaming = false`. If no tokens arrived yet, nothing is pushed but error is still shown.

### `stopStream()`

Calls `abortRef.current?.abort()`. The generator's `AbortError` catch path handles state cleanup.

---

## Stub API (`streamMessage.ts`)

This is the contract FE-08 will implement. The signature must not change.

```ts
// apps/frontend/src/features/chat/api/streamMessage.ts

export async function* streamMessage(
  text: string,
  signal: AbortSignal
): AsyncGenerator<string> {
  const tokens = 'This is a stub response — real answers arrive in FE-08.'.split(' ')
  for (const token of tokens) {
    if (signal.aborted) return
    await new Promise(r => setTimeout(r, 80))
    yield token + ' '
  }
}
```

**FE-08 replaces the body** with a real `fetch` SSE call (reading `data:` lines from the response body). The caller (`useChat`) is unchanged.

---

## ChatThread changes

Two new props added to `ChatThreadProps`:

```ts
interface ChatThreadProps {
  messages: Message[]
  streamingText: string
  isStreaming: boolean
  streamError: string | null
}
```

When `isStreaming` is `true`, an extra assistant message row is rendered at the bottom of the thread:

- `<AssistantMessage text={streamingText} />` — feeds through `MarkdownContent` unchanged
- Below it: three bouncing dots indicator
- When `isStreaming` is `false` and `streamError` is non-null, a small error note renders below the last assistant message

### Bouncing dots

Three `<span>` elements animated with a staggered `translateY` keyframe, using `var(--brand)` fill. Delay: 0ms, 160ms, 320ms.

### Inline error note

```tsx
<p style={{ fontSize: 13, color: 'var(--status-red)', marginTop: 6 }}>
  {streamError}
</p>
```

---

## ChatInput changes

Two new props:

```ts
interface ChatInputProps {
  onSubmit: (text: string) => void
  onStop: () => void
  isStreaming: boolean
}
```

- When `isStreaming` is `false`: submit button renders the send arrow (current behaviour), calls `onSubmit`
- When `isStreaming` is `true`: submit button renders a filled `Square` icon (lucide-react), calls `onStop`; textarea remains editable but `onSubmit` is not callable until streaming stops

---

## Testing

### New tests (9 total)

**`useChat` hook — `src/__tests__/useChat.test.ts` (5 tests)**

1. Appends user message immediately on `sendMessage`
2. Accumulates streamed tokens into the assistant message
3. Moves completed message into `messages` array when stream ends
4. Preserves partial text and clears `isStreaming` when `stopStream` is called
5. Sets `streamError` and preserves partial text on stream failure; error clears on next `sendMessage`

**`ChatThread` — additions to existing test file (2 tests)**

6. Shows bouncing dots and partial text when `isStreaming` is true
7. Hides dots and shows inline error when `isStreaming` is false and `streamError` is set

**`ChatInput` — additions to existing test file (2 tests)**

8. Renders stop (square) button when `isStreaming` is true
9. Renders send button when `isStreaming` is false

---

## Security

No user content is sent to any external service by the stub. When FE-08 replaces the stub, the fetch call will use the internal backend URL — no third-party endpoints.

---

## Out of scope

- Syntax highlighting in code blocks (FE future)
- Multi-turn context management (FE-05)
- Reconnection / retry on stream drop (future)
- Streaming progress percentage or token count
