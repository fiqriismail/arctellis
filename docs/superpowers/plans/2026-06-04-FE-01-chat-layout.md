# FE-01 Chat Layout & Centred Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clean, minimal chat screen with a single auto-resizing text input centred on the page so users can ask questions with no distracting UI chrome.

**Architecture:** A `ChatInput` component in the vertical slice (`src/features/chat/components/`) owns all input state and keyboard handling. The root page wraps it in a centred full-height layout. shadcn/ui's `Textarea` (rather than `Input`) is used so the field can grow for multi-line questions. No testing library is configured yet — verification is visual via `next dev`.

**Tech Stack:** Next.js 16 (App Router) · React 19 · shadcn/ui v4 (base-luma, zinc, light) · Tailwind CSS v4 · lucide-react · TypeScript strict

**Story:** FE-01
**Working directory:** `apps/frontend/` inside repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

**Existing context:**
- `src/app/layout.tsx` — Geist font, light theme, `bg-background` on body
- `src/components/ui/button.tsx` — shadcn Button already present
- `src/features/chat/.gitkeep` — vertical slice directory exists, empty
- `src/app/page.tsx` — placeholder page (to be replaced)
- `src/app/page.module.css` — unused CSS module (to be deleted)
- shadcn configured with `base-luma` style, `zinc` base, CSS variables

---

## File Map

```
apps/frontend/
└── src/
    ├── app/
    │   ├── page.tsx                          ← replace with centred layout (modify)
    │   └── page.module.css                   ← delete (no longer needed)
    ├── components/ui/
    │   └── textarea.tsx                      ← add via shadcn CLI
    └── features/chat/
        └── components/
            └── ChatInput.tsx                 ← new component (create)
```

---

## Task 1: Git branch

- [ ] **Step 1.1: Create feature branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git checkout -b feature/FE-01-chat-layout
```

Expected: `Switched to a new branch 'feature/FE-01-chat-layout'`

---

## Task 2: Add shadcn Textarea component

**Files:**
- Create: `apps/frontend/src/components/ui/textarea.tsx`

- [ ] **Step 2.1: Add the Textarea component via shadcn CLI**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/frontend
npx shadcn@latest add textarea --yes
```

Expected: `✓ Done. textarea added.`

The file `src/components/ui/textarea.tsx` should now exist.

- [ ] **Step 2.2: Verify the file was created**

```bash
cat src/components/ui/textarea.tsx
```

Expected: a React component exporting `Textarea`.

- [ ] **Step 2.3: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/frontend/src/components/ui/textarea.tsx
git commit -m "feat(frontend): add shadcn Textarea component (FE-01)"
```

---

## Task 3: `ChatInput` component

**Files:**
- Create: `apps/frontend/src/features/chat/components/ChatInput.tsx`

- [ ] **Step 3.1: Create the directory**

```bash
mkdir -p /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/frontend/src/features/chat/components
```

- [ ] **Step 3.2: Create `ChatInput.tsx`**

Create `apps/frontend/src/features/chat/components/ChatInput.tsx`:

```tsx
'use client'

import { useEffect, useRef, useState } from 'react'
import { ArrowUp } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface ChatInputProps {
  onSubmit: (question: string) => void
  disabled?: boolean
}

export function ChatInput({ onSubmit, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea as content grows
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [value])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex items-end gap-2">
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about your SharePoint list…"
        rows={1}
        disabled={disabled}
        className="flex-1 resize-none overflow-hidden min-h-[44px]"
      />
      <Button
        onClick={handleSubmit}
        disabled={!value.trim() || disabled}
        size="icon"
        aria-label="Send"
      >
        <ArrowUp className="h-4 w-4" />
      </Button>
    </div>
  )
}
```

- [ ] **Step 3.3: Verify TypeScript compiles cleanly**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3.4: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/frontend/src/features/chat/components/ChatInput.tsx
git commit -m "feat(frontend): add ChatInput component with auto-resize and keyboard submit (FE-01)"
```

---

## Task 4: Centred page layout

**Files:**
- Modify: `apps/frontend/src/app/page.tsx`
- Delete: `apps/frontend/src/app/page.module.css`

- [ ] **Step 4.1: Delete the unused CSS module**

```bash
rm /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/frontend/src/app/page.module.css
```

- [ ] **Step 4.2: Replace `apps/frontend/src/app/page.tsx`**

```tsx
import { ChatInput } from '@/features/chat/components/ChatInput'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">
            SharePoint List AI Assistant
          </h1>
          <p className="text-sm text-muted-foreground">
            Ask a question about your list in plain English.
          </p>
        </div>

        {/* Input */}
        <ChatInput onSubmit={(q) => console.log('Question submitted:', q)} />

        {/* Keyboard hint */}
        <p className="text-center text-xs text-muted-foreground">
          Press <kbd className="rounded border px-1 py-0.5 text-xs font-mono">Enter</kbd> to
          send · <kbd className="rounded border px-1 py-0.5 text-xs font-mono">Shift+Enter</kbd>{' '}
          for new line
        </p>
      </div>
    </div>
  )
}
```

**Note:** `page.tsx` does not have `'use client'` — it is a Server Component. `ChatInput` is `'use client'` so interaction is handled client-side. This pattern is correct for Next.js App Router.

- [ ] **Step 4.3: Verify TypeScript compiles cleanly**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4.4: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/frontend/src/app/page.tsx
git rm apps/frontend/src/app/page.module.css
git commit -m "feat(frontend): centred chat page layout with ChatInput (FE-01)"
```

---

## Task 5: Visual verification + push

- [ ] **Step 5.1: Install deps (if needed) and start dev server**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/frontend
npm install
npm run dev
```

Expected output: `▲ Next.js 16.x.x` and `Local: http://localhost:3000`

- [ ] **Step 5.2: Visual checklist in browser at `http://localhost:3000`**

Verify each item:

- [ ] Page background is white (light theme, `bg-background`)
- [ ] "SharePoint List AI Assistant" heading is centred
- [ ] Textarea input is centred, single-line height initially
- [ ] Placeholder text "Ask a question about your SharePoint list…" visible
- [ ] Send button (↑ arrow) is to the right of the textarea
- [ ] Send button is greyed out when input is empty
- [ ] Typing text enables the Send button
- [ ] Pressing `Enter` on non-empty input logs to browser console and clears the input
- [ ] Pressing `Enter` on empty input does nothing
- [ ] Typing a long message causes the textarea to grow (up to max height)
- [ ] `Shift+Enter` inserts a newline without submitting
- [ ] Page is responsive — looks good on narrow viewport (375px)

- [ ] **Step 5.3: Stop dev server and push**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git push -u origin feature/FE-01-chat-layout
```

---

## Self-Review

**Spec coverage:**

| Acceptance criterion | Task |
|---|---|
| Single, centred text input is the primary control (FR-1) | Task 4: centred layout with ChatInput as sole control |
| No filter panels, dropdowns, or form fields (FR-1) | Task 3/4: no additional controls added |
| Built with shadcn/ui, light theme | Tasks 2/3/4: Textarea, Button from shadcn; CSS variable classes only |
| Submit via button and Enter key; empty submissions prevented | Task 3: `handleSubmit` checks `trimmed`, button `disabled` on empty |
| Responsive, clean layout | Task 4: `max-w-2xl mx-auto px-4`, tested at 375px in Step 5.2 |

**Placeholder scan:** None found.

**Type consistency:**
- `ChatInputProps.onSubmit: (question: string) => void` — consistent between Task 3 definition and Task 4 usage `onSubmit={(q) => ...}`.
- `ChatInputProps.disabled?: boolean` — consistent default `false` in Task 3.
- `Textarea` imported from `@/components/ui/textarea` in Task 3 — created in Task 2.
- `Button` imported from `@/components/ui/button` in Task 3 — pre-existing.
