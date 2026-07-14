# FE-15 — Adopt Arctellis Design System — Design Spec

**Date:** 2026-07-14  
**Status:** Approved

## Overview

Rebrand the chat UI from the current ad hoc SharePoint-blue / RTP-gold token mix to the Arctellis design system (`docs/design-system/repo/`): teal-led palette, azure reserved as a single live-signal accent, Hanken Grotesk + JetBrains Mono type, and the chevron mark. Source of truth for exact values: `docs/design-system/repo/src/Arctellis Design System.dc.html` (or `index.html`, standalone).

Frontend-only change. No backend involvement.

---

## Approach

Two-layer token system: define the Arctellis palette as its own named CSS variables (matching the design system's own token names 1:1), then point the existing shadcn semantic variables at them. This keeps every existing `bg-primary` / `text-foreground` / `focus-within:ring-*` utility working unchanged (no component-by-component rewrite needed for colour), while making the brand values traceable back to the design system by name — the alternative of just overwriting shadcn variable values directly would make the mapping between "primary" and "teal-ink" invisible to future readers.

---

## Token Layer — `globals.css`

### New brand variables (`:root`)

| Variable | Value | Design-system meaning |
|---|---|---|
| `--teal-ink` | `#1F4A57` | Primary, CTAs, logo base |
| `--ink` | `#14323D` | Headings, strongest text |
| `--azure` | `#34A6EB` | Live signal, active states, checks — **one element per view** |
| `--ground` | `#F6F8F8` | Page background |
| `--surface-2` | `#EEF3F3` | Alternating section surface |
| `--border-hairline` | `#DCE5E5` | Hairline rules |
| `--body` | `#46585D` | Body copy |
| `--soft` | `#5A6B70` | Secondary text |
| `--mono` | `#6E8388` | Captions alongside mono figures |
| `--on-teal` | `#CFE0E4` | Body text on teal-ink surfaces |
| `--on-teal-mono` | `#9FC4CE` | Labels on teal-ink surfaces |

### Shadcn semantic remap (`:root`)

- `--background: var(--ground)`
- `--foreground: var(--ink)`
- `--card` / `--popover`: white, unchanged (`oklch(1 0 0)`)
- `--card-foreground` / `--popover-foreground`: `var(--ink)`
- `--primary: var(--teal-ink)`, `--primary-foreground: var(--on-teal)`
- `--secondary` / `--accent`: `var(--surface-2)`, foreground `var(--ink)`
- `--muted: var(--surface-2)`, `--muted-foreground: var(--body)`
- `--border: var(--border-hairline)`, `--input: var(--border-hairline)`
- `--ring: var(--azure)`
- `--destructive`: unchanged (shadcn red) — not part of the brand palette
- Sidebar tokens: mirror the primary mapping (`--sidebar-primary: var(--teal-ink)`, etc.) for consistency, even though the app has no sidebar in current UI

### Removed

- `--brand`, `--brand-strong`, `--brand-tint` (SharePoint blue)
- `--brand-gold`, `--brand-gold-glow`, `--brand-amber` (RTP gold)
- `.input-bar:focus-within` glow switches from `--brand-gold-glow` to an azure-based ring (`box-shadow: 0 0 0 4px rgba(52,166,235,0.18)` or equivalent using `--azure`)

### `.dark` block

Remapped to the reversed palette using the same variable names, even though nothing in the app currently toggles dark mode (kept for forward-compatibility per design system's reversed-lockup guidance):

- `--background: var(--ink)` (`#14323D`), `--foreground: var(--on-teal)`
- `--card` / `--popover`: `var(--teal-ink)`, foreground `var(--on-teal)`
- `--primary: var(--azure)`, `--primary-foreground: var(--ink)`
- `--border` / `--input`: `rgba(255,255,255,0.12)` (hairline on dark, no direct design-system token for this — closest approximation)
- `--muted-foreground: var(--on-teal-mono)`

### Unchanged

- `--chart-1` through `--chart-5` — categorical chart palette, tuned for hue distinctness. Out of scope; not touched by this story.
- `--status-red` / `--status-green` / `--status-amber` (FE-11 status badges) — out of scope, no design-system equivalent defined.
- `--shadow-card-sm/md/lg` — structural shadows, not brand colour, left as-is.

---

## Type — `layout.tsx`

- Replace `Geist` (`next/font/google`) with:
  - `Hanken_Grotesk` — weights `['400','500','600','700','800']`, exposed as `--font-sans`
  - `JetBrains_Mono` — weights `['400','500','600','700']`, exposed as `--font-mono`
- Register `--font-mono` in the `@theme inline` block (`--font-mono: var(--font-mono)`) so `font-mono` becomes a usable Tailwind utility.
- Apply `font-mono` to any element currently rendering a bare figure, label, or eyebrow-style caption: table numeric cells and currency/date formatting (FE-13), status badges (FE-11), timestamps. Scoped to those existing components only — no new components introduced.

---

## Brand Assets

### Header logo — `ChatHeader.tsx`

- Replace `<Image src="/group_one.svg" .../>` + the `RTP Intelligence Hub` text label with the Arctellis lockup image (`arctellis-lockup.png`, copied from `docs/design-system/repo/src/assets/` into `apps/frontend/public/`).
- Drop the vertical divider + separate text label markup since the lockup image is self-contained (wordmark + mark already combined).

### Hero / empty-state icon — `AppIcon.tsx` + `rtp-hub-icon.svg`

- Replace `rtp-hub-icon.svg` (hardcoded `#F6B01C` hexagon + sparkle) with a new SVG built from the chevron mark:
  ```
  path: M50 6 L93 94 L50 71 L7 94 Z
  gradient: #34A6EB → #1F4A57 (linear, vertical, top to bottom)
  viewBox: 0 0 100 100
  ```
  (per design system §04 "Construction" spec, "mark alone / gradient" variant, used for hero/identity contexts).
- Update `alt` text from `"RTP Intelligence Hub"` to `"Arctellis"` — the icon is now the Arctellis mark, and the adjacent `<h1>` already carries the `"RTP Intelligence Hub"` product name, so the two don't need to duplicate.

### Favicon

- New favicon built from the same chevron path, small-size solid-teal or gradient-tile variant per design system §04 "Favicon / app tile" spec: `#14323D` rounded-square background, chevron gradient `#5FBDF2 → #34A6EB`.

---

## Copy Fixes (incidental, in areas already touched)

- `page.tsx` hero subtext: `"...no formulas, no filters — in plain English"` → replace the em dash with a comma or full stop, per the design system's "no em-dashes" convention. This is fixed because the surrounding markup is already being touched for token/colour work, not as a broader copy audit.
- No other copy in the app is audited or changed as part of this story.

---

## Explicitly Out of Scope

- FE-10 (inline style → Tailwind/shadcn migration) is a separate story. Any inline `style={{}}` in `ChatHeader.tsx` / `page.tsx` / `ChatInput.tsx` that already references a CSS variable (`var(--background)`, `var(--border)`, etc.) is left as inline style — it will pick up the new token values automatically. Only inline styles that hard-code a *removed* token (`--brand*`, `--brand-gold*`) are touched, and only at the point of removal.
- Chart colours, status-badge colours (red/green/amber), and card shadows — no design-system equivalent defined, not touched.
- No visual regression tooling exists in this repo; verification is manual (see below).

---

## Verification

Manual check in the dev server across:

1. `ChatHeader` — both states (with and without an active conversation)
2. Empty-state hero (icon, heading, subtext) + suggestion cards
3. Message thread — user/assistant bubbles, markdown rendering
4. `ChatInput` — default and focus states (azure ring, not gold)
5. A data table with status badges and currency/date columns (mono figures)
6. Favicon in browser tab

No automated tests are meaningful for a pure token/asset swap; existing component tests (`ChatHeader.test.tsx`, etc.) should continue to pass unmodified since they don't assert on colour values.

---

## Stories

| ID | Title | Layer |
|---|---|---|
| FE-15 | Adopt Arctellis Design System | Frontend |

### FE-15 — Adopt Arctellis Design System

- Add Arctellis brand variables to `globals.css` `:root` and `.dark`; remap shadcn semantic tokens onto them; remove `--brand*` / `--brand-gold*` / `--brand-amber`
- Update `.input-bar:focus-within` to an azure-based ring
- Swap `Geist` for `Hanken_Grotesk` + `JetBrains_Mono` in `layout.tsx`; register `--font-mono`
- Apply `font-mono` to table figures, status badges, and timestamps
- Copy `arctellis-lockup.png` into `public/`; update `ChatHeader.tsx` to use it in place of `group_one.svg` + text label
- Build a new chevron-based SVG replacing `rtp-hub-icon.svg`; update `AppIcon.tsx` alt text
- Build a new chevron-based favicon
- Fix the em dash in `page.tsx` hero subtext
- Manual verification across header, empty state, thread, input, and a data table

---

## Environment Variables

None. Pure frontend styling/asset change.
