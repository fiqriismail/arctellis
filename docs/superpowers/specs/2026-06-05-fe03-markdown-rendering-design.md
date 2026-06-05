# FE-03 — Markdown Answer Rendering Design

**Date:** 2026-06-05
**Story:** FE-03 Markdown Answer Rendering
**Status:** Approved

---

## Goal

Render assistant answers as rich formatted markdown — headings, lists, tables, emphasis, and code — instead of the current `whiteSpace: pre-wrap` plain text. Rendering must be safe (no unsanitised HTML injection) and visually consistent with the shadcn light theme.

---

## Decisions

| Question | Decision |
|---|---|
| Markdown library | `react-markdown` — converts markdown to React elements with no `dangerouslySetInnerHTML`; safe by default |
| Prose style | Rich (Option B): brand-blue table headers, alternating table rows, tinted inline code, dark code blocks, h2 with border-bottom, blockquote with brand left border |
| Component boundary | New `MarkdownContent` component — extracted from `AssistantMessage` for independent testability and clean separation |
| Props contract | `{ text: string }` — identical to what `AssistantMessage` passes today; FE-04 feeds streamed text in unchanged |
| Syntax highlighting | Out of scope — code blocks use monospace + dark background only |
| Streaming compatibility | `react-markdown` re-renders from the full string each time; partial markdown renders gracefully as plain text until closing delimiters arrive |

---

## Component structure

```
ChatThread.tsx
  └── AssistantMessage
        └── MarkdownContent   ← NEW (replaces plain {text} div)
```

### `MarkdownContent.tsx` — new file

**Location:** `apps/frontend/src/features/chat/components/MarkdownContent.tsx`

**Props:** `{ text: string }`

**Behaviour:** Renders `text` through `react-markdown` with a custom `components` prop. All element styles are applied inline (consistent with existing codebase pattern; FE-10 migrates to Tailwind classes).

**Styled elements:**

| Element | Style |
|---|---|
| `p` | `margin: 0 0 12px`, last child no bottom margin |
| `strong` | `fontWeight: 600` |
| `em` | `fontStyle: italic`, `color: var(--muted-foreground)` |
| `ul`, `ol` | `margin: 8px 0 12px`, `paddingLeft: 22px` |
| `li` | `marginBottom: 5px`, `fontSize: 14.5px` |
| `code` (inline) | `fontFamily: ui-monospace`, `fontSize: 12.5px`, `background: var(--brand-tint)`, `color: var(--brand-strong)`, `padding: 2px 6px`, `borderRadius: 4px`, `border: 1px solid #bfdbfe` |
| `pre` | dark block: `background: #18181b`, `color: #e4e4e7`, `padding: 14px 16px`, `borderRadius: 10px`, `boxShadow: var(--shadow-card-sm)` |
| `h2` | `fontSize: 17px`, `fontWeight: 700`, `borderBottom: 1px solid var(--border)`, `paddingBottom: 5px`, `margin: 16px 0 7px` |
| `h3` | `fontSize: 15px`, `fontWeight: 600`, `margin: 13px 0 6px` |
| `table` | full width, `borderCollapse: collapse`, `fontSize: 13.5px`, `margin: 12px 0` |
| `th` | `background: var(--brand)`, `color: #fff`, `fontWeight: 600`, `padding: 8px 12px` |
| `td` | `padding: 7px 12px`, `borderBottom: 1px solid var(--border)` |
| `blockquote` | `borderLeft: 3px solid var(--brand)`, `background: var(--brand-tint)`, `padding: 6px 12px`, `borderRadius: 0 6px 6px 0`, `fontStyle: italic` |

### `ChatThread.tsx` change

In `AssistantMessage`, replace:

```tsx
<div style={{ fontSize: 14.5, lineHeight: 1.62, color: 'var(--foreground)', whiteSpace: 'pre-wrap' }}>
  {text}
</div>
```

With:

```tsx
<MarkdownContent text={text} />
```

---

## Security

`react-markdown` parses markdown and builds a React element tree — it never calls `dangerouslySetInnerHTML` for markdown content. Raw HTML tags in the markdown source are stripped by default (`allowDangerousHtml` is `false` unless explicitly set). This satisfies the "no unsanitised HTML injection" acceptance criterion.

---

## Streaming compatibility

`react-markdown` accepts a plain string and re-renders the full React tree on each update. When FE-04 feeds partial streamed text, incomplete markdown constructs (e.g. an unclosed `**`, a table missing its closing row) render as plain text until the closing delimiter arrives. No special handling is needed in `MarkdownContent` for FE-03.

---

## Testing

New file: `apps/frontend/src/__tests__/MarkdownContent.test.tsx`

Tests:
1. Renders a paragraph
2. Renders `**bold**` as `<strong>`
3. Renders `_italic_` as `<em>`
4. Renders an unordered list
5. Renders an ordered list
6. Renders inline `code` with brand-tint styling
7. Renders a fenced code block
8. Renders an `## h2` heading
9. Renders a markdown table

---

## New dependency

| Package | Version | Reason |
|---|---|---|
| `react-markdown` | `^9.0` | Markdown → React element tree, safe by default |

No other new packages. `@tailwindcss/typography` is not required.

---

## Files changed

| File | Change |
|---|---|
| `apps/frontend/package.json` | Add `react-markdown` dependency |
| `apps/frontend/src/features/chat/components/MarkdownContent.tsx` | New — markdown renderer |
| `apps/frontend/src/features/chat/components/ChatThread.tsx` | `AssistantMessage` uses `<MarkdownContent>` |
| `apps/frontend/src/__tests__/MarkdownContent.test.tsx` | New — 9 tests |

---

## Out of scope

- Syntax highlighting in code blocks (future story)
- GFM task lists (`- [ ]`) — out of scope for FE-03
- Image rendering (`![alt](url)`) — out of scope
- Raw HTML pass-through — explicitly disabled for security
