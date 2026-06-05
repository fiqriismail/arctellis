# FE-02 — Conversation Thread Design

**Date:** 2026-06-05
**Story:** [FE-02 Conversation Thread Rendering](../../../apps/frontend/src/features/chat/)
**Status:** Approved

---

## Goal

Render a vertical conversation thread that shows the exchange between the user and the assistant. The thread replaces the empty state once the first message is submitted.

---

## Decisions

| Question | Decision |
|---|---|
| Thread layout | Reference-faithful: user bubbles right-aligned, assistant turns left-aligned with brand avatar |
| Props contract | `ChatThread` takes a `messages: Message[]` prop — no internal state or fetch logic |
| Suggestion cards | Wire up to `handleSubmit` in FE-02 so clicking a card transitions to the thread |
| Stub responses | `handleSubmit` appends a user message then a static stub assistant message so the full thread is visible; FE-04 replaces the stub with a real streaming call |
| New chat button | Out of scope — FE-06 |
| Typing indicator | Out of scope — FE-04 |
| Markdown rendering | Out of scope — FE-03 |

---

## Message type

New file: `apps/frontend/src/features/chat/types.ts`

```ts
export type UserMessage      = { role: 'user';      text: string }
export type AssistantMessage = { role: 'assistant'; text: string }
export type Message          = UserMessage | AssistantMessage
```

Kept minimal so FE-04 can extend `AssistantMessage` (e.g. add `thinking?: boolean`) without breaking anything already built.

---

## Component structure

```
page.tsx                          ← state owner
  ├── [messages.length === 0]
  │     EmptyState (existing)     ← suggestion cards now call handleSubmit
  └── [messages.length > 0]
        ChatHeader                ← no changes
        ChatThread                ← NEW, flex-1, overflow-y-auto
          ├── UserMessage         ← right-aligned bubble (inline sub-component)
          └── AssistantMessage    ← left-aligned with avatar (inline sub-component)
        docked composer           ← ChatInput with border-top blur strip
```

### `page.tsx` changes

- Add `const [messages, setMessages] = useState<Message[]>([])`
- `handleSubmit(text: string)`:
  1. Appends `{ role: 'user', text }`
  2. Appends stub `{ role: 'assistant', text: 'Connected to the backend in FE-08 — real answers will appear here.' }`
- Pass `onSubmit={handleSubmit}` to `ChatInput` and to each suggestion card's `onClick`
- Conditionally render empty state vs chat layout based on `messages.length`

### `ChatThread.tsx` — new file

**Props:** `{ messages: Message[] }`

**Behaviour:**
- `useRef` on the scroll container; `useEffect([messages])` scrolls to bottom on every new message using `scrollIntoView({ behavior: 'smooth' })` on a sentinel `<div>` at the bottom
- Renders `UserMessage` or `AssistantMessage` for each item

**Layout (chat state):**
```
<div style="height:100%; display:flex; flex-direction:column">
  <ChatHeader />                       ← sticky, no change
  <div ref={scrollRef} flex-1 overflow-y-auto>
    <div maxWidth=780 margin=auto padding=28px 24px>
      {messages.map(...)}
    </div>
  </div>
  <div border-top blur-bg>             ← docked composer strip
    <div maxWidth=780 margin=auto padding=14px 24px 16px>
      <ChatInput compact onSubmit={handleSubmit} />
    </div>
  </div>
</div>
```

### `UserMessage`

```
Right-aligned flex row
  └── bubble: max-width 78%, bg muted, padding 10px 15px,
              border-radius 16px 16px 4px 16px, font-size 14.5px
```

Animation: `msgIn` — `opacity 0 → 1, translateY 8px → 0` over `0.34s` (matches reference; respects `prefers-reduced-motion`). The keyframe is added to `globals.css`; gated behind `@media (prefers-reduced-motion: no-preference)`.

### `AssistantMessage`

```
Left-aligned flex row, gap 13px
  ├── avatar: 30×30, border-radius 8, bg brand, spark icon 16px
  └── body: flex-1
        └── prose text: font-size 14.5px, line-height 1.62
```

Animation: same `msgIn` as user message.

---

## Auto-scroll

`useEffect` fires on every `messages` change. Scrolls a `<div ref={bottomRef} />` sentinel at the end of the list into view with `behavior: 'smooth'`. This is correct for FE-02; FE-04 will refine to avoid scrolling when the user has manually scrolled up mid-stream.

---

## Stub assistant response

For FE-02, `handleSubmit` adds a hardcoded placeholder:

```
"Connected to the backend in FE-08 — real answers will appear here."
```

This makes the thread testable end-to-end without a backend. FE-04 replaces this entirely with the SSE streaming call.

---

## Files changed

| File | Change |
|---|---|
| `apps/frontend/src/features/chat/types.ts` | New — `Message` union type |
| `apps/frontend/src/features/chat/components/ChatThread.tsx` | New — thread renderer |
| `apps/frontend/src/app/page.tsx` | Add messages state, handleSubmit, conditional layout |

---

## Out of scope

- Typing / loading indicator (FE-04)
- Markdown / rich answer rendering (FE-03)
- "New chat" button (FE-06)
- Copy button on assistant messages (FE-06)
- Session persistence (FE-05)
