# FE-06 — New Conversation Control: Design Spec

**Date:** 2026-06-05
**Story:** FE-06 New Conversation Control
**Status:** Approved

---

## Overview

Add a "New conversation" button to the chat header that immediately clears the visible thread and resets the backend session context. No confirmation dialog — the click is intentional, the action is instant.

---

## Architecture & Data Flow

No new files. Two existing files change; one new test file is added.

```
features/chat/components/ChatHeader.tsx   — add optional onNewConversation prop + button
app/page.tsx                              — destructure resetSession, pass to ChatHeader
__tests__/ChatHeader.test.tsx             — new: button render and click tests
__tests__/page.test.tsx                   — add integration test (button clears thread)
```

**Data flow:**
1. `useChat()` in `page.tsx` returns `resetSession` (implemented in FE-05).
2. In the conversation view branch (`messages.length > 0`), `page.tsx` passes `onNewConversation={resetSession}` to `ChatHeader`.
3. Clicking the button calls `resetSession` → clears `messages`, `streamingText`, `streamError`, `isStreaming`, rotates `sessionId`.
4. With `messages` now empty, the page drops back to the landing/empty state. The button disappears naturally (the empty-state `<ChatHeader />` receives no prop).
5. The empty-state branch in `page.tsx` passes no `onNewConversation` prop — header renders without the button.

---

## Component Changes

### `ChatHeader.tsx`

Add an optional prop and a shadcn `Button` (ghost, sm) in the top-right of the header:

```tsx
interface ChatHeaderProps {
  onNewConversation?: () => void
}

export function ChatHeader({ onNewConversation }: ChatHeaderProps) {
  return (
    <header ...existing styles...>
      {/* existing logo/title markup unchanged */}
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

- Uses `lucide-react`'s `Plus` icon and shadcn `Button` — consistent with the rest of the UI.
- Button renders only when `onNewConversation` is provided; absent on the empty/landing state.

### `page.tsx`

Two minimal changes:
1. Destructure `resetSession` from `useChat()`.
2. Pass `onNewConversation={resetSession}` to `<ChatHeader />` in the `messages.length > 0` branch only.

The empty-state `<ChatHeader />` (no messages) is left unchanged.

---

## Testing

### `__tests__/ChatHeader.test.tsx` (new file)

| Test | Description |
|---|---|
| No button without prop | `render(<ChatHeader />)` → "New conversation" button absent |
| Button visible with prop | `render(<ChatHeader onNewConversation={fn} />)` → button present |
| Click calls handler | Click button → `onNewConversation` called once |

### `__tests__/page.test.tsx` (addition)

| Test | Description |
|---|---|
| New conversation button clears thread | After a message exchange, clicking "New conversation" removes the thread and restores the landing heading |

---

## Constraints

- **Immediate clear** — no confirmation dialog. The header placement makes the action intentional.
- **Button only in conversation view** — absent on the landing/empty state (no conversation to clear).
- **shadcn `Button` + lucide `Plus`** — no custom button styles; matches existing UI conventions.
- **`resetSession` is not re-implemented** — FE-06 is purely a wiring story on top of FE-05.
