---
tag: todo
component: front-end
created: 2026-06-05
---

# FE-10 Migrate Inline Styles to shadcn/ui

## Goal

Replace the inline `style={{}}` props introduced during design-matching (FE-01 polish) with proper shadcn/ui component primitives and Tailwind CSS utility classes, in line with the project's coding conventions.

## Background

During FE-01 layout polish, several components were written with inline styles to achieve pixel-accurate fidelity to the reference design ([[SharePoint List AI Assistant.html]]):

- `ChatHeader.tsx` — header layout, icon box, branding text
- `ChatInput.tsx` — composer wrapper, textarea, send button, Kbd hint
- `page.tsx` — hero icon, empty-state container, suggestion cards

Inline styles bypass the design system and make theming, dark mode, and future refactors harder.

## Acceptance criteria

- [ ] All `style={{}}` props removed from `ChatHeader`, `ChatInput`, and `page.tsx`
- [ ] Colours reference CSS variable utility classes (`bg-background`, `text-foreground`, `text-muted-foreground`, etc.) or the custom `--brand` / `--shadow-card-*` tokens via Tailwind arbitrary values
- [ ] shadcn `Button` used for the send button with appropriate variant / `className` overrides for the active/disabled colour swap
- [ ] shadcn `Textarea` used in `ChatInput` (with default styles stripped via `className`)
- [ ] Visual output matches the current design pixel-for-pixel (screenshot diff as part of review)
- [ ] No new hard-coded hex values introduced; any design-token colours live in `globals.css` `:root`

## Notes

- The `--brand`, `--border-strong`, `--muted-2`, `--shadow-card-*` CSS variables added in FE-01 polish should be exposed in `@theme inline` so Tailwind can generate utility classes (e.g. `bg-brand`, `shadow-card-md`)
- The focus ring on `ChatInput` (brand blue, 3px spread) can be expressed as a Tailwind `focus-within:` variant once the token is registered
- Suggestion card hover state (`translateY(-1px)`, shadow upgrade) can use `hover:` utilities
