# FE-03 Markdown Answer Rendering — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace plain `whiteSpace: pre-wrap` text in `AssistantMessage` with a `MarkdownContent` component that renders rich formatted markdown using `react-markdown`.

**Architecture:** A new `MarkdownContent` component wraps `react-markdown` with a custom `components` prop that applies rich prose styles inline (brand-blue table headers, tinted inline code, dark code blocks, h2 with border-bottom, blockquote with brand left border). `AssistantMessage` inside `ChatThread.tsx` imports and uses it, replacing the plain text `<div>`. All styling is inline to match the existing codebase pattern.

**Tech Stack:** `react-markdown ^10.0.0`, `remark-gfm ^4.0.0`, React 19, TypeScript strict, Jest 30 + React Testing Library.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `apps/frontend/package.json` | Modify | Add `react-markdown` and `remark-gfm` dependencies |
| `apps/frontend/src/features/chat/components/MarkdownContent.tsx` | Create | Markdown → React element tree with rich prose styles |
| `apps/frontend/src/__tests__/MarkdownContent.test.tsx` | Create | 9 unit tests covering all styled elements |
| `apps/frontend/src/features/chat/components/ChatThread.tsx` | Modify | `AssistantMessage` uses `<MarkdownContent>` instead of plain `{text}` |

---

## Task 1: Install `react-markdown` and `remark-gfm`

**Files:**
- Modify: `apps/frontend/package.json`

- [ ] **Step 1: Install packages**

Run from `apps/frontend/`:

```bash
npm install react-markdown@^10.0.0 remark-gfm@^4.0.0
```

Expected: packages added to `dependencies` in `package.json`, `package-lock.json` updated, no errors.

- [ ] **Step 2: Verify the install**

```bash
node -e "require('react-markdown'); console.log('ok')"
```

Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add apps/frontend/package.json apps/frontend/package-lock.json
git commit -m "chore(frontend): add react-markdown and remark-gfm (FE-03)"
```

---

## Task 2: `MarkdownContent` component (TDD)

**Files:**
- Create: `apps/frontend/src/__tests__/MarkdownContent.test.tsx`
- Create: `apps/frontend/src/features/chat/components/MarkdownContent.tsx`

### Step 1 — Write the failing tests

- [ ] **Create `apps/frontend/src/__tests__/MarkdownContent.test.tsx`:**

```tsx
import { render, screen } from '@testing-library/react'
import { MarkdownContent } from '@/features/chat/components/MarkdownContent'

describe('MarkdownContent', () => {
  it('renders a paragraph', () => {
    render(<MarkdownContent text="Hello world" />)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
  })

  it('renders bold text as <strong>', () => {
    render(<MarkdownContent text="**bold text**" />)
    const el = document.querySelector('strong')
    expect(el).toBeInTheDocument()
    expect(el).toHaveTextContent('bold text')
  })

  it('renders italic text as <em>', () => {
    render(<MarkdownContent text="_italic text_" />)
    const el = document.querySelector('em')
    expect(el).toBeInTheDocument()
    expect(el).toHaveTextContent('italic text')
  })

  it('renders an unordered list', () => {
    render(<MarkdownContent text={'- item one\n- item two'} />)
    expect(document.querySelector('ul')).toBeInTheDocument()
    expect(screen.getByText('item one')).toBeInTheDocument()
    expect(screen.getByText('item two')).toBeInTheDocument()
  })

  it('renders an ordered list', () => {
    render(<MarkdownContent text={'1. first\n2. second'} />)
    expect(document.querySelector('ol')).toBeInTheDocument()
    expect(screen.getByText('first')).toBeInTheDocument()
  })

  it('renders inline code', () => {
    render(<MarkdownContent text={'Use `console.log` to debug'} />)
    const code = document.querySelector('code')
    expect(code).toBeInTheDocument()
    expect(code).toHaveTextContent('console.log')
  })

  it('renders a fenced code block inside <pre>', () => {
    render(<MarkdownContent text={'```\nconst x = 1;\n```'} />)
    const pre = document.querySelector('pre')
    expect(pre).toBeInTheDocument()
    expect(pre).toHaveTextContent('const x = 1;')
  })

  it('renders an h2 heading', () => {
    render(<MarkdownContent text="## Summary" />)
    expect(document.querySelector('h2')).toBeInTheDocument()
    expect(screen.getByText('Summary')).toBeInTheDocument()
  })

  it('renders a GFM table', () => {
    const md = '| Name | Age |\n|---|---|\n| Alice | 30 |'
    render(<MarkdownContent text={md} />)
    expect(document.querySelector('table')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run to confirm 9 failures**

```bash
cd apps/frontend && npx jest MarkdownContent --no-coverage
```

Expected: 9 tests fail with "Cannot find module '@/features/chat/components/MarkdownContent'".

### Step 3 — Implement `MarkdownContent`

- [ ] **Create `apps/frontend/src/features/chat/components/MarkdownContent.tsx`:**

```tsx
'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'

const components: Components = {
  p({ children }) {
    return <p style={{ margin: '0 0 12px' }}>{children}</p>
  },
  strong({ children }) {
    return <strong style={{ fontWeight: 600 }}>{children}</strong>
  },
  em({ children }) {
    return <em style={{ fontStyle: 'italic', color: 'var(--muted-foreground)' }}>{children}</em>
  },
  ul({ children }) {
    return <ul style={{ margin: '8px 0 12px', paddingLeft: 22 }}>{children}</ul>
  },
  ol({ children }) {
    return <ol style={{ margin: '8px 0 12px', paddingLeft: 22 }}>{children}</ol>
  },
  li({ children }) {
    return <li style={{ marginBottom: 5, fontSize: 14.5 }}>{children}</li>
  },
  code({ className, children }) {
    const isBlock = /language-(\w+)/.test(className || '') || String(children).includes('\n')
    if (isBlock) {
      return (
        <code style={{ fontFamily: 'ui-monospace, monospace', fontSize: 'inherit' }}>
          {children}
        </code>
      )
    }
    return (
      <code style={{
        fontFamily: 'ui-monospace, monospace',
        fontSize: 12.5,
        background: 'var(--brand-tint)',
        color: 'var(--brand-strong)',
        padding: '2px 6px',
        borderRadius: 4,
        border: '1px solid #bfdbfe',
      }}>
        {children}
      </code>
    )
  },
  pre({ children }) {
    return (
      <pre style={{
        background: '#18181b',
        color: '#e4e4e7',
        padding: '14px 16px',
        borderRadius: 10,
        fontSize: 12.5,
        overflowX: 'auto',
        margin: '12px 0',
        fontFamily: 'ui-monospace, monospace',
        lineHeight: 1.6,
        boxShadow: '0 2px 8px rgba(0,0,0,.15)',
      }}>
        {children}
      </pre>
    )
  },
  h2({ children }) {
    return (
      <h2 style={{
        fontSize: 17,
        fontWeight: 700,
        margin: '16px 0 7px',
        color: 'var(--foreground)',
        letterSpacing: '-0.01em',
        paddingBottom: 5,
        borderBottom: '1px solid var(--border)',
      }}>
        {children}
      </h2>
    )
  },
  h3({ children }) {
    return (
      <h3 style={{
        fontSize: 15,
        fontWeight: 600,
        margin: '13px 0 6px',
        color: 'var(--foreground)',
      }}>
        {children}
      </h3>
    )
  },
  table({ children }) {
    return (
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: 13.5,
        margin: '12px 0',
      }}>
        {children}
      </table>
    )
  },
  th({ children }) {
    return (
      <th style={{
        background: 'var(--brand)',
        color: '#fff',
        fontWeight: 600,
        textAlign: 'left',
        padding: '8px 12px',
      }}>
        {children}
      </th>
    )
  },
  td({ children }) {
    return (
      <td style={{
        padding: '7px 12px',
        borderBottom: '1px solid var(--border)',
        color: 'var(--foreground)',
      }}>
        {children}
      </td>
    )
  },
  blockquote({ children }) {
    return (
      <blockquote style={{
        borderLeft: '3px solid var(--brand)',
        margin: '10px 0',
        padding: '6px 12px',
        background: 'var(--brand-tint)',
        borderRadius: '0 6px 6px 0',
        color: 'var(--muted-foreground)',
        fontStyle: 'italic',
      }}>
        {children}
      </blockquote>
    )
  },
}

interface MarkdownContentProps {
  text: string
}

export function MarkdownContent({ text }: MarkdownContentProps) {
  return (
    <div style={{ fontSize: 14.5, lineHeight: 1.68, color: 'var(--foreground)' }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {text}
      </ReactMarkdown>
    </div>
  )
}
```

- [ ] **Step 4: Run to confirm all 9 pass**

```bash
cd apps/frontend && npx jest MarkdownContent --no-coverage
```

Expected: `9 passed, 9 total`.

- [ ] **Step 5: Run the full suite to check for regressions**

```bash
cd apps/frontend && npx jest --no-coverage
```

Expected: all existing tests still pass (ChatThread ×5, HomePage ×4, MarkdownContent ×9 = 18 total).

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/features/chat/components/MarkdownContent.tsx \
        apps/frontend/src/__tests__/MarkdownContent.test.tsx
git commit -m "feat(frontend): add MarkdownContent component with rich prose styles (FE-03)"
```

---

## Task 3: Wire `MarkdownContent` into `AssistantMessage`

**Files:**
- Modify: `apps/frontend/src/features/chat/components/ChatThread.tsx`

The current `AssistantMessage` body (lines ~68–76) renders plain text:

```tsx
<div style={{
  fontSize: 14.5,
  lineHeight: 1.62,
  color: 'var(--foreground)',
  whiteSpace: 'pre-wrap',
}}>
  {text}
</div>
```

- [ ] **Step 1: Add the import at the top of `ChatThread.tsx`**

After the existing imports, add:

```tsx
import { MarkdownContent } from '@/features/chat/components/MarkdownContent'
```

Full imports section will be:

```tsx
'use client'

import { useRef, useEffect } from 'react'
import { Sparkles } from 'lucide-react'
import { Message } from '@/features/chat/types'
import { MarkdownContent } from '@/features/chat/components/MarkdownContent'
```

- [ ] **Step 2: Replace the plain text `<div>` inside `AssistantMessage`**

Remove:

```tsx
<div style={{
  fontSize: 14.5,
  lineHeight: 1.62,
  color: 'var(--foreground)',
  whiteSpace: 'pre-wrap',
}}>
  {text}
</div>
```

Replace with:

```tsx
<MarkdownContent text={text} />
```

The full `AssistantMessage` function after the change:

```tsx
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

- [ ] **Step 3: Run the full test suite**

```bash
cd apps/frontend && npx jest --no-coverage
```

Expected: 18 tests pass — ChatThread ×5, HomePage ×4, MarkdownContent ×9.

- [ ] **Step 4: Commit**

```bash
git add apps/frontend/src/features/chat/components/ChatThread.tsx
git commit -m "feat(frontend): render assistant messages as markdown (FE-03)"
```

---

## Self-check: TypeScript

After all tasks, verify there are no type errors:

```bash
cd apps/frontend && npx tsc --noEmit
```

Expected: no errors.

If TypeScript complains about `react-markdown` or `remark-gfm` types, both packages ship their own types — no `@types/*` packages are needed.
