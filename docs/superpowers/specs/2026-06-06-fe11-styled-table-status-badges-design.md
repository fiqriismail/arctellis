# FE-11 Styled Table Rendering with Status Badges — Design

**Story:** FE-11  
**Date:** 2026-06-06  
**Status:** Approved

---

## Overview

Replace the hand-rolled inline-style table overrides in `MarkdownContent` with shadcn `Table` + `Badge` primitives. Tables rendered from Markdown answers gain rounded corners, a muted header, alternating row stripes, and coloured status badges for known RTP status values.

---

## Components installed

```
npx shadcn add table badge
```

Adds to `src/components/ui/`:
- `table.tsx` — `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`, `TableCaption`
- `badge.tsx` — `Badge` with variants: `default`, `secondary`, `destructive`, `outline`

---

## New file: `StatusBadge`

**Path:** `src/features/chat/components/StatusBadge.tsx`

A pure presentational component. Receives a string value, looks it up (case-insensitive) in a known-status map, and returns a `<Badge>` with the appropriate variant. Unknown values render as plain text (no badge).

### Status → variant mapping

| Value | Variant |
|---|---|
| Draft | `secondary` |
| Submitted | `default` |
| Under SME Review | `warning` |
| Budget Confirmation | `warning` |
| Exception Required | `warning` |
| Sourcing in Progress | `default` |
| Approved for PO | `success` |
| Approved | `success` |
| Closed | `secondary` |
| Rejected | `destructive` |

### Custom variants added to `badge.tsx`

Two variants not in shadcn's default set are added directly to the `badgeVariants` cva config:

- **`success`** — `bg-green-100 text-green-800 border-green-200` (light theme only; uses Tailwind colour utilities since no CSS variable covers semantic green in shadcn zinc)
- **`warning`** — `bg-amber-100 text-amber-800 border-amber-200`

---

## Updated file: `MarkdownContent.tsx`

### Table wrapper

```tsx
table({ children }) {
  return (
    <div className="my-3 w-full overflow-x-auto rounded-lg border">
      <Table>{children}</Table>
    </div>
  )
}
```

The `rounded-lg border overflow-x-auto` wrapper provides the rounded corners and horizontal scroll on narrow viewports. The inner `<Table>` handles `w-full text-sm`.

### thead / tbody / tr

```tsx
thead({ children }) { return <TableHeader>{children}</TableHeader> }
tbody({ children }) { return <TableBody>{children}</TableBody> }
tr({ children })   { return <TableRow>{children}</TableRow> }
```

`<TableRow>` applies `even:bg-muted/40` for alternating stripe (built into shadcn's default).

### th

```tsx
th({ children }) {
  return <TableHead className="bg-muted font-semibold">{children}</TableHead>
}
```

Header uses `bg-muted` (shadcn's muted token — light gray) instead of the previous brand-colour background.

### td

```tsx
td({ children }) {
  const text = typeof children === 'string' ? children : null
  return (
    <TableCell>
      {text ? <StatusBadge value={text} /> : children}
    </TableCell>
  )
}
```

When the cell content is a plain string, it is passed through `StatusBadge`. If `StatusBadge` does not recognise the value it renders the text unchanged.

---

## Testing

### Existing tests

All tests in `src/__tests__/MarkdownContent.test.tsx` must remain green. They assert on rendered text content, not CSS classes, so they are unaffected by the component swap.

### New tests (added to same file)

| Test | Assertion |
|---|---|
| Known status value renders as badge | Cell containing `"Active"` renders a `<span>` with role/class indicating a badge, not bare text |
| Badge variant reflects status semantics | `"Rejected"` gets `destructive` class, `"Approved"` gets `success` class |
| Unknown value renders as plain text | `"Some random text"` in a cell renders without badge markup |
| Case-insensitive match | `"approved"` and `"APPROVED"` both render as success badge |
| Table has rounded wrapper | Rendered table is wrapped in a `div` with class `rounded-lg` |

---

## Out of scope

- Dark mode badge colours (deferred — app is light theme only per CLAUDE.md)
- Sorting or filtering within the table
- Pagination
