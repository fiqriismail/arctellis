# FE-11 Styled Table Rendering with Status Badges — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hand-rolled inline-style table overrides in `MarkdownContent` with shadcn `Table` + `Badge` primitives, adding rounded corners, muted header, alternating row stripes, and coloured status badges for known RTP status values.

**Architecture:** Install shadcn `table` and `badge` components, extend `badge.tsx` with `success` and `warning` variants, create a `StatusBadge` helper component, then rewire all table-related overrides in `MarkdownContent.tsx` to use the new primitives.

**Tech Stack:** Next.js App Router, shadcn/ui v4, Tailwind CSS v4, ReactMarkdown + remark-gfm, Jest + React Testing Library.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create (via shadcn CLI) | `src/components/ui/table.tsx` | shadcn Table primitives |
| Create (via shadcn CLI) | `src/components/ui/badge.tsx` | shadcn Badge + custom `success`/`warning` variants |
| Create | `src/features/chat/components/StatusBadge.tsx` | Maps known status strings → Badge variant |
| Modify | `src/features/chat/components/MarkdownContent.tsx` | Wire shadcn Table + StatusBadge into overrides |
| Modify | `src/__tests__/MarkdownContent.test.tsx` | Add table structure + badge behaviour tests |

---

## Task 1: Install shadcn `table` and `badge` components

**Files:**
- Create: `src/components/ui/table.tsx`
- Create: `src/components/ui/badge.tsx`

- [ ] **Step 1: Run the shadcn CLI**

From `apps/frontend/`:

```bash
npx shadcn add table badge
```

Accept all prompts. This writes both component files into `src/components/ui/`.

- [ ] **Step 2: Verify files exist**

```bash
ls src/components/ui/
```

Expected output includes: `badge.tsx  button.tsx  table.tsx  textarea.tsx`

- [ ] **Step 3: Run existing tests to confirm nothing broke**

```bash
npm test -- --testPathPattern=MarkdownContent
```

Expected: all existing tests PASS (we haven't touched anything yet).

---

## Task 2: Add `success` and `warning` variants to `badge.tsx`

**Files:**
- Modify: `src/components/ui/badge.tsx`

shadcn's default Badge ships with `default`, `secondary`, `destructive`, `outline`. We need `success` (green) and `warning` (amber).

- [ ] **Step 1: Open `src/components/ui/badge.tsx` and locate the `badgeVariants` cva block**

It will look roughly like:

```tsx
const badgeVariants = cva(
  "...",
  {
    variants: {
      variant: {
        default: "...",
        secondary: "...",
        destructive: "...",
        outline: "...",
      },
    },
    ...
  }
)
```

- [ ] **Step 2: Add `success` and `warning` to the variant map**

Inside the `variant` object, add after `outline`:

```tsx
success:
  "border-green-200 bg-green-100 text-green-800",
warning:
  "border-amber-200 bg-amber-100 text-amber-800",
```

- [ ] **Step 3: Run tests — still green**

```bash
npm test -- --testPathPattern=MarkdownContent
```

Expected: PASS (nothing uses these variants yet).

- [ ] **Step 4: Commit**

```bash
git add src/components/ui/table.tsx src/components/ui/badge.tsx
git commit -m "feat(frontend): install shadcn table and badge, add success/warning variants (FE-11)"
```

---

## Task 3: Create `StatusBadge` component (TDD)

**Files:**
- Test: `src/__tests__/MarkdownContent.test.tsx`
- Create: `src/features/chat/components/StatusBadge.tsx`

- [ ] **Step 1: Write failing tests for StatusBadge**

Add a new `describe` block at the bottom of `src/__tests__/MarkdownContent.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '@/features/chat/components/StatusBadge'

describe('StatusBadge', () => {
  it('renders a badge for a known status value', () => {
    render(<StatusBadge value="Active" />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders plain text for an unknown value', () => {
    const { container } = render(<StatusBadge value="Some random text" />)
    // No badge element — just a text node wrapped in a span
    expect(container.firstChild).toHaveTextContent('Some random text')
    expect(container.querySelector('[class*="badge"]')).toBeNull()
  })

  it('is case-insensitive — lowercase matches', () => {
    render(<StatusBadge value="approved" />)
    expect(screen.getByText('approved')).toBeInTheDocument()
  })

  it('is case-insensitive — uppercase matches', () => {
    render(<StatusBadge value="REJECTED" />)
    expect(screen.getByText('REJECTED')).toBeInTheDocument()
  })

  it('renders Rejected with destructive styling', () => {
    const { container } = render(<StatusBadge value="Rejected" />)
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toMatch(/destructive/)
  })

  it('renders Approved with success styling', () => {
    const { container } = render(<StatusBadge value="Approved" />)
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toMatch(/success/)
  })

  it('renders Under SME Review with warning styling', () => {
    const { container } = render(<StatusBadge value="Under SME Review" />)
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toMatch(/warning/)
  })

  it('renders Draft with secondary styling', () => {
    const { container } = render(<StatusBadge value="Draft" />)
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toMatch(/secondary/)
  })
})
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
npm test -- --testPathPattern=MarkdownContent
```

Expected: FAIL — `Cannot find module '@/features/chat/components/StatusBadge'`

- [ ] **Step 3: Create `StatusBadge.tsx`**

Create `src/features/chat/components/StatusBadge.tsx`:

```tsx
import { Badge } from '@/components/ui/badge'
import type { VariantProps } from 'class-variance-authority'

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'

const STATUS_MAP: Record<string, BadgeVariant> = {
  'draft':                'secondary',
  'submitted':            'default',
  'under sme review':     'warning',
  'budget confirmation':  'warning',
  'exception required':   'warning',
  'sourcing in progress': 'default',
  'approved for po':      'success',
  'approved':             'success',
  'closed':               'secondary',
  'rejected':             'destructive',
  'active':               'success',
}

interface StatusBadgeProps {
  value: string
}

export function StatusBadge({ value }: StatusBadgeProps) {
  const variant = STATUS_MAP[value.toLowerCase()]
  if (!variant) {
    return <span>{value}</span>
  }
  return <Badge variant={variant as any}>{value}</Badge>
}
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
npm test -- --testPathPattern=MarkdownContent
```

Expected: all StatusBadge tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/features/chat/components/StatusBadge.tsx src/__tests__/MarkdownContent.test.tsx
git commit -m "feat(frontend): add StatusBadge component with RTP status-to-variant mapping (FE-11)"
```

---

## Task 4: Update `MarkdownContent` table overrides (TDD)

**Files:**
- Test: `src/__tests__/MarkdownContent.test.tsx`
- Modify: `src/features/chat/components/MarkdownContent.tsx`

- [ ] **Step 1: Write failing tests for the new table structure**

Add a second new `describe` block in `src/__tests__/MarkdownContent.test.tsx` (after the StatusBadge block):

```tsx
describe('MarkdownContent table rendering', () => {
  const TABLE_MD = '| Title | Status |\n|---|---|\n| Laptop | Active |\n| Chair | Draft |'

  it('wraps table in a rounded border container', () => {
    const { container } = render(<MarkdownContent text={TABLE_MD} />)
    const wrapper = container.querySelector('div.rounded-lg')
    expect(wrapper).toBeInTheDocument()
    expect(wrapper?.querySelector('table')).toBeInTheDocument()
  })

  it('renders status cell as a badge', () => {
    render(<MarkdownContent text={TABLE_MD} />)
    // "Active" should be inside a badge, not bare text in a td
    const active = screen.getByText('Active')
    expect(active.tagName).not.toBe('TD')
  })

  it('renders non-status cell as plain text', () => {
    render(<MarkdownContent text={TABLE_MD} />)
    expect(screen.getByText('Laptop')).toBeInTheDocument()
  })

  it('renders table header cells', () => {
    render(<MarkdownContent text={TABLE_MD} />)
    expect(screen.getByText('Title')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests — confirm new tests fail**

```bash
npm test -- --testPathPattern=MarkdownContent
```

Expected: the two new table tests FAIL (`div.rounded-lg` not found; `Active` still renders as bare td text).

- [ ] **Step 3: Rewrite table-related overrides in `MarkdownContent.tsx`**

Replace the file's imports and `components` object entries for `table`, `th`, `td` — and add `thead`, `tbody`, `tr` — as follows.

At the top of the file, add imports after the existing ones:

```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { StatusBadge } from './StatusBadge'
```

Replace the `table`, `th`, and `td` entries in `components`, and add `thead`, `tbody`, `tr`:

```tsx
  table({ children }) {
    return (
      <div className="my-3 w-full overflow-x-auto rounded-lg border">
        <Table>{children}</Table>
      </div>
    )
  },
  thead({ children }) {
    return <TableHeader>{children}</TableHeader>
  },
  tbody({ children }) {
    return <TableBody>{children}</TableBody>
  },
  tr({ children }) {
    return <TableRow>{children}</TableRow>
  },
  th({ children }) {
    return <TableHead className="bg-muted font-semibold">{children}</TableHead>
  },
  td({ children }) {
    const text =
      typeof children === 'string'
        ? children
        : Array.isArray(children) && children.length === 1 && typeof children[0] === 'string'
          ? children[0]
          : null
    return (
      <TableCell>
        {text !== null ? <StatusBadge value={text} /> : children}
      </TableCell>
    )
  },
```

Remove the old `table`, `th`, `td` entries entirely — they are fully replaced by the above.

- [ ] **Step 4: Run all MarkdownContent tests**

```bash
npm test -- --testPathPattern=MarkdownContent
```

Expected: ALL tests PASS — original tests, StatusBadge tests, and new table tests.

- [ ] **Step 5: Commit**

```bash
git add src/features/chat/components/MarkdownContent.tsx src/__tests__/MarkdownContent.test.tsx
git commit -m "feat(frontend): styled table with shadcn Table primitives and StatusBadge (FE-11)"
```

---

## Task 5: Full test run + mark story done

- [ ] **Step 1: Run the full test suite**

```bash
npm test
```

Expected: ALL tests PASS, no warnings.

- [ ] **Step 2: Mark FE-11 done in Obsidian**

```bash
obsidian vault="Group One RTP" property:set name="tag" value="done" file="FE-11 Styled Table Rendering with Status Badges"
obsidian vault="Group One RTP" daily:append content="- Completed FE-11 Styled Table Rendering with Status Badges — shadcn Table + Badge primitives in MarkdownContent, custom success/warning badge variants, StatusBadge for RTP status values"
```

- [ ] **Step 3: Update the Story Board**

```bash
obsidian vault="Group One RTP" read file="Story Board - Frontend"
```

Find the FE-11 row and change its status from `` `todo` `` to `` `done` ``.

```bash
obsidian vault="Group One RTP" append file="Story Board - Frontend" content=""
```

(Use the Obsidian CLI `property:set` or manual edit via the vault UI to update the status in the table.)
