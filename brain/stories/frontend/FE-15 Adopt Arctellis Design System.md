---
tag: todo
component: front-end
created: 2026-07-14
---

# FE-15 Adopt Arctellis Design System

## Goal

Rebrand the chat UI to the Arctellis design system ([[docs/design-system/repo/README.md|design-system/repo]]): teal-led palette, Hanken Grotesk + JetBrains Mono type, azure reserved as a single live-signal accent, and UK-English/no-em-dash copy — replacing the current ad hoc SharePoint-blue / RTP-gold tokens in `globals.css`.

## Background

`globals.css` currently mixes shadcn defaults with two unrelated brand token sets bolted on during earlier stories:

- `--brand` / `--brand-strong` / `--brand-tint` — SharePoint blue (`#0f6cbd`)
- `--brand-gold` / `--brand-gold-glow` / `--brand-amber` — RTP hub gold, used for the `ChatInput` focus ring

Neither matches the Arctellis brand system delivered in `docs/design-system/repo/`. That system specifies:

- **Colour** — `--teal-ink` `#1F4A57` (primary/CTAs/logo base), `--ink` `#14323D` (headings), `--azure` `#34A6EB` (single live accent only — never decorative/structural), `--ground` `#F6F8F8` (page bg), `--surface-2` `#EEF3F3`, `--border` `#DCE5E5`, `--body` `#46585D`, plus `--soft` `#5A6B70`, `--mono` `#6E8388`, and on-teal text pair `#CFE0E4` / `#9FC4CE`.
- **Type** — Hanken Grotesk (400–800) for all display/body copy; JetBrains Mono (400–700) for every figure, label and eyebrow (so numbers read as computed, not claimed). Currently the app loads only `Geist` via `next/font/google` (`layout.tsx`).
- **Iconography** — the north-pointing chevron motif (gradient construction documented in section 04).
- **Voice & tone** — UK English throughout, no em-dashes (comma or full stop instead), azure used for exactly one live element per view.

This is a system-wide token swap, not a component-by-component rewrite — most components already consume CSS variables via [[FE-10 Migrate Inline Styles to shadcn UI]]-style utility classes, so the bulk of the work is remapping tokens at the `:root` level and auditing usages that assumed the old brand hues.

## Acceptance criteria

- [ ] `globals.css` `:root` (and `.dark`, if a dark variant is kept) updated to the Arctellis palette; `--brand*` / `--brand-gold*` / `--brand-amber` tokens removed or renamed to the equivalent Arctellis tokens (`--teal-ink`, `--azure`, `--ground`, `--surface-2`, `--border`, `--body`, `--soft`, `--mono`)
- [ ] shadcn theme mapping (`--primary`, `--ring`, `--accent`, etc. in `@theme inline`) points at the new tokens so existing `bg-primary` / `text-foreground` / `focus-within:ring-*` usages pick up the rebrand automatically
- [ ] Hanken Grotesk (400–800) and JetBrains Mono (400–700) loaded via `next/font/google` in `layout.tsx`, replacing `Geist`; `--font-sans` / a new `--font-mono` exposed for Tailwind
- [ ] Every place currently rendering a figure, label, or eyebrow-style caption (amounts, dates, badges, counts) uses the mono font utility, per the design system's "figures always computed, not claimed" rule
- [ ] `ChatInput` focus ring recoloured from `--brand-gold-glow` to azure, and audited so azure appears on at most one live element per view (no blanket azure fills/backgrounds)
- [ ] App logo / header icon swapped for the Arctellis lockup or chevron mark (assets in `docs/design-system/repo/src/assets/`), respecting documented clear space and minimum size
- [ ] No hard-coded hex values left outside `globals.css` `:root`
- [ ] Any user-facing copy touched by this story follows UK English / no-em-dash conventions
- [ ] Visual regression check across chat header, message thread, input bar, tables, and empty-state suggestion cards

## Notes

- Reference file for exact values and specimens: `docs/design-system/repo/src/Arctellis Design System.dc.html` (editable source) or `docs/design-system/repo/index.html` (standalone, opens in any browser, no build step).
- Chart colours (`--chart-1..5`) are out of scope for hue changes unless they visually clash with the new teal/azure palette — flag rather than silently reassign, since they're tuned for categorical distinctness.
- Do this after [[FE-10 Migrate Inline Styles to shadcn UI]] if that is still pending — remapping tokens is far simpler once components no longer carry ad hoc inline colours.
