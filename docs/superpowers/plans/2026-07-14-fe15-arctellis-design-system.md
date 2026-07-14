# FE-15 Adopt Arctellis Design System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand the chat UI from the current ad hoc SharePoint-blue / RTP-gold token mix to the Arctellis design system (teal-led palette, azure single-signal accent, Hanken Grotesk + JetBrains Mono, chevron mark).

**Architecture:** Two-layer CSS variable system in `globals.css` — new Arctellis brand tokens (`--teal-ink`, `--azure`, `--ground`, etc.) defined once, existing shadcn semantic tokens (`--primary`, `--background`, `--ring`, etc.) remapped to reference them via `var()`. This lets every existing Tailwind utility (`bg-primary`, `text-foreground`, `focus-within:ring-*`) pick up the rebrand without per-component rewrites. A handful of components hard-code the old token names directly (`var(--brand-gold)`, `var(--brand-amber)`, etc., found by grep) and are fixed individually.

**Tech Stack:** Next.js App Router, Tailwind CSS v4 (`@theme inline` + CSS custom properties), shadcn/ui, `next/font/google`, Jest + Testing Library.

## Global Constraints

- No hard-coded hex values outside `globals.css` `:root` (spec requirement).
- Azure (`--azure` / `#34A6EB`) is reserved for exactly one live-signal element per view — never a structural fill or background (design system rule, spec section "Token Layer").
- UK English, no em-dashes in any copy touched by this story (spec requirement).
- `--chart-1` through `--chart-5`, `--status-red/green/amber`, `--shadow-card-*` are explicitly out of scope — do not modify (spec "Unchanged" section).
- FE-10 (inline-style migration) is a separate story — only touch inline styles that reference a token being removed in this story; leave all other inline styles as-is.
- All commands below run from `apps/frontend/` unless stated otherwise.

---

### Task 1: Token layer — remap `globals.css` to the Arctellis palette

**Files:**
- Modify: `apps/frontend/src/app/globals.css`

**Interfaces:**
- Produces: CSS custom properties `--teal-ink`, `--ink`, `--azure`, `--ground`, `--surface-2`, `--border-hairline`, `--body`, `--soft`, `--mono`, `--on-teal`, `--on-teal-mono` on `:root`, consumed by Tasks 3–8.
- Produces: shadcn semantic tokens (`--primary`, `--background`, `--foreground`, `--border`, `--ring`, `--muted-foreground`, etc.) now aliasing the above — consumed automatically by every existing `bg-*`/`text-*`/`border-*` Tailwind utility across the app.
- Removes: `--brand`, `--brand-strong`, `--brand-tint`, `--brand-gold`, `--brand-gold-glow`, `--brand-amber` — Tasks 3 and 4 must no longer reference these names after this task.

- [ ] **Step 1: Replace the `:root` block**

Find this block in `apps/frontend/src/app/globals.css` (lines 85–141):

```css
:root {
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  /* SharePoint brand */
  --brand: #0f6cbd;
  --brand-strong: #0a5ca8;
  --brand-tint: #eff6fc;
  /* RTP hub brand */
  --brand-gold: #f6b01c;
  --brand-gold-glow: rgba(246, 176, 28, 0.22);
  --brand-amber: #c9820a;
  --ink: #1b1b1f;
  /* extended border */
  --border-strong: #d4d4d8;
  /* extra muted surface */
  --muted-2: #fafafa;
  /* status colours */
  --status-red: #b42318;
  --status-green: #16794c;
  --status-amber: #9a6a00;
  /* design-system shadows */
  --shadow-card-sm: 0 1px 2px 0 rgba(9,9,11,.05);
  --shadow-card-md: 0 4px 12px -2px rgba(9,9,11,.08), 0 2px 4px -2px rgba(9,9,11,.04);
  --shadow-card-lg: 0 12px 32px -8px rgba(9,9,11,.16), 0 4px 8px -4px rgba(9,9,11,.06);
  --secondary: oklch(0.97 0 0);
  --secondary-foreground: oklch(0.205 0 0);
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.556 0 0);
  --accent: oklch(0.97 0 0);
  --accent-foreground: oklch(0.205 0 0);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.922 0 0);
  --input: oklch(0.922 0 0);
  --ring: oklch(0.708 0 0);
  /* Categorical chart palette (distinct hues, not greyscale) */
  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);
  --radius: 0.625rem;
  --sidebar: oklch(0.985 0 0);
  --sidebar-foreground: oklch(0.145 0 0);
  --sidebar-primary: oklch(0.205 0 0);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.97 0 0);
  --sidebar-accent-foreground: oklch(0.205 0 0);
  --sidebar-border: oklch(0.922 0 0);
  --sidebar-ring: oklch(0.708 0 0);
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  color-scheme: light dark;
}
```

Replace it with:

```css
:root {
  /* Arctellis brand palette — see docs/design-system/repo */
  --teal-ink: #1F4A57;
  --ink: #14323D;
  --azure: #34A6EB;
  --ground: #F6F8F8;
  --surface-2: #EEF3F3;
  --border-hairline: #DCE5E5;
  --body: #46585D;
  --soft: #5A6B70;
  --mono: #6E8388;
  --on-teal: #CFE0E4;
  --on-teal-mono: #9FC4CE;

  /* shadcn semantic tokens, aliased to the brand palette above */
  --card: oklch(1 0 0);
  --card-foreground: var(--ink);
  --popover: oklch(1 0 0);
  --popover-foreground: var(--ink);
  --primary: var(--teal-ink);
  --primary-foreground: var(--on-teal);
  --secondary: var(--surface-2);
  --secondary-foreground: var(--ink);
  --muted: var(--surface-2);
  --muted-foreground: var(--body);
  --accent: var(--surface-2);
  --accent-foreground: var(--ink);
  --destructive: oklch(0.577 0.245 27.325);
  --border: var(--border-hairline);
  --input: var(--border-hairline);
  --ring: var(--azure);
  --background: var(--ground);
  --foreground: var(--ink);

  /* extended border */
  --border-strong: #d4d4d8;
  /* extra muted surface */
  --muted-2: #fafafa;
  /* status colours */
  --status-red: #b42318;
  --status-green: #16794c;
  --status-amber: #9a6a00;
  /* design-system shadows */
  --shadow-card-sm: 0 1px 2px 0 rgba(9,9,11,.05);
  --shadow-card-md: 0 4px 12px -2px rgba(9,9,11,.08), 0 2px 4px -2px rgba(9,9,11,.04);
  --shadow-card-lg: 0 12px 32px -8px rgba(9,9,11,.16), 0 4px 8px -4px rgba(9,9,11,.06);
  /* Categorical chart palette (distinct hues, not greyscale) — out of scope, unchanged */
  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);
  --radius: 0.625rem;
  --sidebar: oklch(0.985 0 0);
  --sidebar-foreground: var(--ink);
  --sidebar-primary: var(--teal-ink);
  --sidebar-primary-foreground: var(--on-teal);
  --sidebar-accent: var(--surface-2);
  --sidebar-accent-foreground: var(--ink);
  --sidebar-border: var(--border-hairline);
  --sidebar-ring: var(--azure);
  color-scheme: light dark;
}
```

- [ ] **Step 2: Replace the `.dark` block**

Find this block (immediately follows `:root`):

```css
.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.205 0 0);
  --card-foreground: oklch(0.985 0 0);
  --popover: oklch(0.205 0 0);
  --popover-foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
  --secondary: oklch(0.269 0 0);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.269 0 0);
  --muted-foreground: oklch(0.708 0 0);
  --accent: oklch(0.269 0 0);
  --accent-foreground: oklch(0.985 0 0);
  --destructive: oklch(0.704 0.191 22.216);
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.556 0 0);
  /* Categorical chart palette (distinct hues, not greyscale) */
  --chart-1: oklch(0.488 0.243 264.376);
  --chart-2: oklch(0.696 0.17 162.48);
  --chart-3: oklch(0.769 0.188 70.08);
  --chart-4: oklch(0.627 0.265 303.9);
  --chart-5: oklch(0.645 0.246 16.439);
  --sidebar: oklch(0.205 0 0);
  --sidebar-foreground: oklch(0.985 0 0);
  --sidebar-primary: oklch(0.488 0.243 264.376);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.269 0 0);
  --sidebar-accent-foreground: oklch(0.985 0 0);
  --sidebar-border: oklch(1 0 0 / 10%);
  --sidebar-ring: oklch(0.556 0 0);
}
```

Replace it with:

```css
.dark {
  --background: var(--ink);
  --foreground: var(--on-teal);
  --card: var(--teal-ink);
  --card-foreground: var(--on-teal);
  --popover: var(--teal-ink);
  --popover-foreground: var(--on-teal);
  --primary: var(--azure);
  --primary-foreground: var(--ink);
  --secondary: var(--teal-ink);
  --secondary-foreground: var(--on-teal);
  --muted: var(--teal-ink);
  --muted-foreground: var(--on-teal-mono);
  --accent: var(--teal-ink);
  --accent-foreground: var(--on-teal);
  --destructive: oklch(0.704 0.191 22.216);
  --border: rgba(255, 255, 255, 0.12);
  --input: rgba(255, 255, 255, 0.16);
  --ring: var(--azure);
  /* Categorical chart palette (distinct hues, not greyscale) — out of scope, unchanged */
  --chart-1: oklch(0.488 0.243 264.376);
  --chart-2: oklch(0.696 0.17 162.48);
  --chart-3: oklch(0.769 0.188 70.08);
  --chart-4: oklch(0.627 0.265 303.9);
  --chart-5: oklch(0.645 0.246 16.439);
  --sidebar: var(--teal-ink);
  --sidebar-foreground: var(--on-teal);
  --sidebar-primary: var(--azure);
  --sidebar-primary-foreground: var(--ink);
  --sidebar-accent: var(--teal-ink);
  --sidebar-accent-foreground: var(--on-teal);
  --sidebar-border: rgba(255, 255, 255, 0.12);
  --sidebar-ring: var(--azure);
}
```

- [ ] **Step 3: Recolour the input focus ring from gold to azure**

Find:

```css
.input-bar:focus-within {
  border-color: var(--brand-gold);
  box-shadow: 0 0 0 4px var(--brand-gold-glow);
  outline: none;
}
```

Replace with:

```css
.input-bar:focus-within {
  border-color: var(--azure);
  box-shadow: 0 0 0 4px rgba(52, 166, 235, 0.18);
  outline: none;
}
```

- [ ] **Step 4: Verify no remaining references to removed tokens in this file**

Run: `grep -n "brand-gold\|brand-amber\|brand-tint\|brand-strong\|--brand:" apps/frontend/src/app/globals.css`
Expected: no output (all removed in Steps 1–3).

- [ ] **Step 5: Run the full test suite to confirm no regressions**

Run: `cd apps/frontend && npm test`
Expected: all existing suites pass (this task only changes CSS variable values, no test asserts on colour).

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/app/globals.css
git commit -m "feat(frontend): remap colour tokens to Arctellis palette (FE-15)"
```

---

### Task 2: Typography — load Hanken Grotesk + JetBrains Mono

**Files:**
- Modify: `apps/frontend/src/app/layout.tsx`
- Modify: `apps/frontend/src/app/globals.css`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `--font-sans` and `--font-mono` CSS variables carrying real font-family values (previously `--font-sans` was referenced in `@theme inline` but never actually set by `next/font`, silently falling back to Tailwind's default stack). Tasks 3, 5, and 6 depend on `font-mono` being a working Tailwind utility after this task.

- [ ] **Step 1: Replace the font import and instantiation in `layout.tsx`**

Find:

```tsx
import type { Metadata } from 'next'
import { Geist } from 'next/font/google'
import './globals.css'
import { Providers } from './Providers'

const geist = Geist({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Group One RTP — AI Assistant',
  description: 'Ask questions about your SharePoint list in plain English.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={geist.className} suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

Replace with:

```tsx
import type { Metadata } from 'next'
import { Hanken_Grotesk, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { Providers } from './Providers'

const hankenGrotesk = Hanken_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-sans',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: 'Group One RTP — AI Assistant',
  description: 'Ask questions about your SharePoint list in plain English.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${hankenGrotesk.variable} ${jetbrainsMono.variable}`}
        suppressHydrationWarning
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

(Note: the page `<title>` still says "Group One RTP" — that's the browser tab title for the existing product name, unrelated to the Arctellis visual rebrand, and out of scope per the spec.)

- [ ] **Step 2: Register `--font-mono` in the `@theme inline` block of `globals.css`**

Find (near the top of `globals.css`):

```css
@theme inline {
  --font-heading: var(--font-sans);
  --font-sans: var(--font-sans);
  --color-sidebar-ring: var(--sidebar-ring);
```

Replace with:

```css
@theme inline {
  --font-heading: var(--font-sans);
  --font-sans: var(--font-sans);
  --font-mono: var(--font-mono);
  --color-sidebar-ring: var(--sidebar-ring);
```

- [ ] **Step 3: Start the dev server and confirm the fonts load**

Run: `cd apps/frontend && npm run dev`
Open `http://localhost:3000` in a browser, open DevTools → Network → Font, and confirm `HankenGrotesk` and `JetBrainsMono` font files are requested (not `Geist`). Stop the dev server after confirming (Ctrl+C).

- [ ] **Step 4: Run the full test suite to confirm no regressions**

Run: `cd apps/frontend && npm test`
Expected: all existing suites pass.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/app/layout.tsx apps/frontend/src/app/globals.css
git commit -m "feat(frontend): load Hanken Grotesk + JetBrains Mono (FE-15)"
```

---

### Task 3: Composer & thread live-signal accents — azure replaces gold/amber

**Files:**
- Modify: `apps/frontend/src/features/chat/components/ChatInput.tsx`
- Modify: `apps/frontend/src/features/chat/components/ChatThread.tsx`
- Test: `apps/frontend/src/__tests__/ChatInput.test.tsx` (existing, must still pass unmodified)

**Interfaces:**
- Consumes: `--azure` from Task 1, `--font-mono` utility from Task 2.
- Produces: no new interfaces — internal styling only.

**Design system rule this task applies:** azure is reserved for exactly one live-signal element per view. The composer's active send button and the streaming typing-indicator dots are both "is something happening right now" cues — the same category of usage the design system calls out by name ("the analysing pulse, an active check"). They don't compete because a user only ever sees the composer button (idle vs. ready-to-send) or the typing indicator (only visible while the assistant is streaming) as the live cue in view at a given moment.

- [ ] **Step 1: Recolour the send/stop button and switch the keyboard hint to mono**

Find in `apps/frontend/src/features/chat/components/ChatInput.tsx`:

```tsx
        <button
          onClick={isStreaming ? handleStop : handleSubmit}
          disabled={!buttonActive}
          aria-label={isStreaming ? 'Stop' : 'Send'}
          style={{
            width: 34, height: 34, flexShrink: 0, borderRadius: 9,
            border: 'none', cursor: buttonActive ? 'pointer' : 'default',
            background: buttonActive ? 'var(--brand-gold)' : '#e4e4e7',
            color: buttonActive ? 'var(--ink)' : '#a1a1aa',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background .15s', marginBottom: 1,
          }}
        >
```

Replace with:

```tsx
        <button
          onClick={isStreaming ? handleStop : handleSubmit}
          disabled={!buttonActive}
          aria-label={isStreaming ? 'Stop' : 'Send'}
          style={{
            width: 34, height: 34, flexShrink: 0, borderRadius: 9,
            border: 'none', cursor: buttonActive ? 'pointer' : 'default',
            background: buttonActive ? 'var(--azure)' : '#e4e4e7',
            color: buttonActive ? '#ffffff' : '#a1a1aa',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background .15s', marginBottom: 1,
          }}
        >
```

Find (in the same file, the `Kbd` helper):

```tsx
function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd style={{
      fontFamily: 'ui-monospace, "SF Mono", monospace',
      fontSize: 11, padding: '1.5px 5px', borderRadius: 5,
      background: 'var(--muted)', border: '1px solid var(--border)',
      color: 'var(--muted-foreground)', boxShadow: '0 1px 0 var(--border)',
    }}>{children}</kbd>
  )
}
```

Replace with:

```tsx
function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd style={{
      fontFamily: 'var(--font-mono)',
      fontSize: 11, padding: '1.5px 5px', borderRadius: 5,
      background: 'var(--muted)', border: '1px solid var(--border)',
      color: 'var(--muted-foreground)', boxShadow: '0 1px 0 var(--border)',
    }}>{children}</kbd>
  )
}
```

- [ ] **Step 2: Recolour the streaming typing indicator**

Find in `apps/frontend/src/features/chat/components/ChatThread.tsx`:

```tsx
        <span
          key={i}
          style={{
            display: 'inline-block',
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: 'var(--brand-amber)',
            animation: `typingBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
```

Replace with:

```tsx
        <span
          key={i}
          style={{
            display: 'inline-block',
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: 'var(--azure)',
            animation: `typingBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
```

- [ ] **Step 3: Run the affected tests**

Run: `cd apps/frontend && npm test -- ChatInput ChatThread`
Expected: all pass (these tests assert on button roles/labels and streaming behaviour, not colour, so no test changes are needed).

- [ ] **Step 4: Grep to confirm no remaining `--brand-gold`/`--brand-amber` references anywhere in the app**

Run: `cd apps/frontend && grep -rn "brand-gold\|brand-amber" src`
Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/features/chat/components/ChatInput.tsx apps/frontend/src/features/chat/components/ChatThread.tsx
git commit -m "feat(frontend): recolour composer/typing-indicator live signal to azure (FE-15)"
```

---

### Task 4: Markdown content — blockquote and inline code tokens

**Files:**
- Modify: `apps/frontend/src/features/chat/components/MarkdownContent.tsx`

**Interfaces:**
- Consumes: `--teal-ink`, `--surface-2` from Task 1.
- Produces: no new interfaces.

- [ ] **Step 1: Recolour inline code**

Find in `apps/frontend/src/features/chat/components/MarkdownContent.tsx`:

```tsx
    return (
      <code style={{
        fontFamily: 'ui-monospace, monospace',
        fontSize: 12.5,
        background: 'var(--brand-tint)',
        color: 'var(--brand-strong)',
        padding: '2px 6px',
        borderRadius: 4,
        border: '1px solid var(--border)',
      }}>
        {children}
      </code>
    )
```

Replace with:

```tsx
    return (
      <code style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 12.5,
        background: 'var(--surface-2)',
        color: 'var(--teal-ink)',
        padding: '2px 6px',
        borderRadius: 4,
        border: '1px solid var(--border)',
      }}>
        {children}
      </code>
    )
```

- [ ] **Step 2: Recolour the blockquote**

Find:

```tsx
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
```

Replace with:

```tsx
  blockquote({ children }) {
    return (
      <blockquote style={{
        borderLeft: '3px solid var(--teal-ink)',
        margin: '10px 0',
        padding: '6px 12px',
        background: 'var(--surface-2)',
        borderRadius: '0 6px 6px 0',
        color: 'var(--muted-foreground)',
        fontStyle: 'italic',
      }}>
        {children}
      </blockquote>
    )
  },
```

- [ ] **Step 3: Grep to confirm no remaining `--brand`/`--brand-tint`/`--brand-strong` references anywhere in the app**

Run: `cd apps/frontend && grep -rn "var(--brand)" src && grep -rn "brand-tint\|brand-strong" src`
Expected: no output (both commands return nothing — if `grep` finds no match it exits non-zero, so seeing no printed lines is success).

- [ ] **Step 4: Run the full test suite**

Run: `cd apps/frontend && npm test`
Expected: all existing suites pass.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/features/chat/components/MarkdownContent.tsx
git commit -m "feat(frontend): recolour markdown code/blockquote to Arctellis tokens (FE-15)"
```

---

### Task 5: Table & badge mono figures

**Files:**
- Modify: `apps/frontend/src/features/chat/components/DataTable.tsx`
- Modify: `apps/frontend/src/components/ui/badge.tsx`
- Test: `apps/frontend/src/__tests__/DataTable.test.tsx` (existing, must still pass unmodified)

**Interfaces:**
- Consumes: `--font-mono` Tailwind utility from Task 2.
- Produces: no new interfaces.

**Design system rule this task applies:** "JetBrains Mono handles every figure, label and eyebrow, so numbers always look computed rather than claimed." Numeric table cells (currency/number/integer) and status badges are exactly this category.

- [ ] **Step 1: Add `font-mono` to numeric table cells**

Find in `apps/frontend/src/features/chat/components/DataTable.tsx`:

```tsx
                  <TableCell
                    key={ci}
                    className={`border-r border-border text-[13px] last:border-r-0 ${
                      c.numeric ? 'text-right tabular-nums' : ''
                    }`}
                  >
```

Replace with:

```tsx
                  <TableCell
                    key={ci}
                    className={`border-r border-border text-[13px] last:border-r-0 ${
                      c.numeric ? 'text-right tabular-nums font-mono' : ''
                    }`}
                  >
```

- [ ] **Step 2: Add `font-mono` to the badge base styles**

Find in `apps/frontend/src/components/ui/badge.tsx`:

```tsx
const badgeVariants = cva(
  "group/badge inline-flex h-5 w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-3xl border border-transparent px-2 py-0.5 text-xs font-medium whitespace-nowrap transition-all focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&>svg]:pointer-events-none [&>svg]:size-3!",
```

Replace with:

```tsx
const badgeVariants = cva(
  "group/badge inline-flex h-5 w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-3xl border border-transparent px-2 py-0.5 text-xs font-mono font-medium whitespace-nowrap transition-all focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&>svg]:pointer-events-none [&>svg]:size-3!",
```

- [ ] **Step 3: Run the affected tests**

Run: `cd apps/frontend && npm test -- DataTable`
Expected: all pass — the tests assert on text content and the `text-right` class substring via regex, both unaffected by adding `font-mono`.

- [ ] **Step 4: Run the full test suite**

Run: `cd apps/frontend && npm test`
Expected: all existing suites pass.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/features/chat/components/DataTable.tsx apps/frontend/src/components/ui/badge.tsx
git commit -m "feat(frontend): use JetBrains Mono for table figures and badges (FE-15)"
```

---

### Task 6: Header logo — swap to the Arctellis lockup

**Files:**
- Create: `apps/frontend/public/arctellis-lockup.png` (copied from design system assets)
- Modify: `apps/frontend/src/features/chat/components/ChatHeader.tsx`
- Test: `apps/frontend/src/__tests__/ChatHeader.test.tsx` (existing, must still pass unmodified — it only asserts on the "New conversation" button, not the logo)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: no new interfaces.

- [ ] **Step 1: Copy the lockup asset into the frontend's public directory**

Run (from the repo root):

```bash
cp "docs/design-system/repo/src/assets/arctellis-lockup.png" apps/frontend/public/arctellis-lockup.png
```

- [ ] **Step 2: Replace the logo + divider + text label with the lockup image**

Find in `apps/frontend/src/features/chat/components/ChatHeader.tsx`:

```tsx
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Image
          src="/group_one.svg"
          alt="group.one"
          width={142}
          height={26}
          priority
        />
        <span aria-hidden style={{ width: 1, height: 20, background: 'var(--border)' }} />
        <span style={{ fontSize: 14.5, fontWeight: 600, letterSpacing: '-.01em' }}>
          RTP Intelligence Hub
        </span>
      </div>
```

Replace with:

```tsx
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Image
          src="/arctellis-lockup.png"
          alt="Arctellis"
          width={118}
          height={28}
          priority
        />
      </div>
```

(The lockup PNG is 420×100px, an aspect ratio of 4.2:1; 118×28 keeps that ratio at a height comparable to the previous 26px-tall logo. The wordmark is already part of the lockup image, so the separate divider and "RTP Intelligence Hub" text label are removed — the `<h1>` on the empty-state screen, untouched by this task, still carries that product name.)

- [ ] **Step 3: Run the affected test**

Run: `cd apps/frontend && npm test -- ChatHeader`
Expected: pass (test only checks the "New conversation" button, unaffected by the logo swap).

- [ ] **Step 4: Start the dev server and visually confirm the header**

Run: `cd apps/frontend && npm run dev`
Open `http://localhost:3000`, confirm the Arctellis lockup renders correctly in the header (not stretched, not blurry). Stop the server (Ctrl+C).

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/public/arctellis-lockup.png apps/frontend/src/features/chat/components/ChatHeader.tsx
git commit -m "feat(frontend): replace header logo with Arctellis lockup (FE-15)"
```

---

### Task 7: Hero icon and copy fix

**Files:**
- Modify: `apps/frontend/public/rtp-hub-icon.svg`
- Modify: `apps/frontend/src/components/AppIcon.tsx`
- Modify: `apps/frontend/src/app/page.tsx`
- Test: `apps/frontend/src/__tests__/page.test.tsx` (existing, must still pass unmodified)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: no new interfaces.

- [ ] **Step 1: Replace the hero icon SVG with the Arctellis chevron mark**

Find the full contents of `apps/frontend/public/rtp-hub-icon.svg`:

```svg
<svg width="64" height="64" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RTP Intelligence Hub">
  <title>RTP Intelligence Hub</title>
  
  <path d="M50 12 L82.91 31 L82.91 69 L50 88 L17.09 69 L17.09 31 Z" fill="#F6B01C" stroke="#F6B01C" stroke-width="11" stroke-linejoin="round"></path>
  
  <g fill="#1B1B1F">
    <path transform="translate(47,52) scale(2.3) translate(-12,-12)" d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .962 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.962 0z"></path>
    <path transform="translate(72.5,31) scale(0.62) translate(-12,-12)" d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .962 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.962 0z"></path>
  </g>
</svg>
```

Replace with (chevron construction per `docs/design-system/repo/src/Arctellis Design System.dc.html`, "mark alone / gradient" variant):

```svg
<svg width="64" height="64" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Arctellis">
  <title>Arctellis</title>
  <defs>
    <linearGradient id="arctellisMark" x1="50" y1="0" x2="50" y2="100" gradientUnits="userSpaceOnUse">
      <stop stop-color="#34A6EB"/>
      <stop offset="1" stop-color="#1F4A57"/>
    </linearGradient>
  </defs>
  <path d="M50 6 L93 94 L50 71 L7 94 Z" fill="url(#arctellisMark)"/>
</svg>
```

- [ ] **Step 2: Update `AppIcon`'s alt text**

Find in `apps/frontend/src/components/AppIcon.tsx`:

```tsx
    <Image
      src="/rtp-hub-icon.svg"
      alt="RTP Intelligence Hub"
      width={size}
      height={size}
      priority={priority}
    />
```

Replace with:

```tsx
    <Image
      src="/rtp-hub-icon.svg"
      alt="Arctellis"
      width={size}
      height={size}
      priority={priority}
    />
```

- [ ] **Step 3: Fix the em dash in the hero subtext**

Find in `apps/frontend/src/app/page.tsx`:

```tsx
                <p style={{ fontSize: 15.5, color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.5 }}>
                  Ask anything about your{' '}
                  <span style={{ fontWeight: 550, color: 'var(--foreground)' }}>purchase requests</span>
                  {' '}in plain English — no formulas, no filters.
                </p>
```

Replace with:

```tsx
                <p style={{ fontSize: 15.5, color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.5 }}>
                  Ask anything about your{' '}
                  <span style={{ fontWeight: 550, color: 'var(--foreground)' }}>purchase requests</span>
                  {' '}in plain English, no formulas, no filters.
                </p>
```

- [ ] **Step 4: Run the affected test**

Run: `cd apps/frontend && npm test -- page.test`
Expected: pass. The placeholder-text assertion uses the regex `/ask a question/i`, which still matches the unchanged `ChatInput` placeholder — this task doesn't touch that placeholder.

- [ ] **Step 5: Start the dev server and visually confirm the hero icon**

Run: `cd apps/frontend && npm run dev`
Open `http://localhost:3000` with no conversation started, confirm the chevron mark renders (azure-to-teal gradient, no gold hexagon). Stop the server (Ctrl+C).

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/public/rtp-hub-icon.svg apps/frontend/src/components/AppIcon.tsx apps/frontend/src/app/page.tsx
git commit -m "feat(frontend): replace hero icon with Arctellis chevron mark (FE-15)"
```

---

### Task 8: Favicon — chevron mark

**Files:**
- Modify: `apps/frontend/src/app/icon.svg`
- Delete: `apps/frontend/src/app/favicon.ico`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: no new interfaces.

**Note on scope:** `favicon.ico` is a binary multi-resolution ICO file that can't be hand-authored as text. Since Next.js App Router serves `icon.svg` as the favicon when no `favicon.ico` is present, and all evergreen browsers support SVG favicons, this task removes the stale gold-icon `favicon.ico` rather than regenerating an equivalent ICO — avoiding a second, inconsistent brand icon shipping alongside the new SVG one. If pixel-perfect `.ico` support for legacy browsers is later required, that needs image-generation tooling outside this repo's toolchain and should be a follow-up, not part of this story.

- [ ] **Step 1: Replace `icon.svg` with the chevron favicon tile**

Find the full contents of `apps/frontend/src/app/icon.svg` (same gold hexagon-sparkle icon as `rtp-hub-icon.svg`, different rounding):

```svg
<svg width="64" height="64" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RTP Intelligence Hub">
  <title>RTP Intelligence Hub</title>
  
  <path d="M50 12 L82.91 31 L82.91 69 L50 88 L17.09 69 L17.09 31 Z" fill="#F6B01C" stroke="#F6B01C" stroke-width="11" stroke-linejoin="round"></path>
  
  <g fill="#1B1B1F">
    <path transform="translate(47,52) scale(2.3) translate(-12,-12)" d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .962 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.962 0z"></path>
    <path transform="translate(72.5,31) scale(0.62) translate(-12,-12)" d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .962 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.962 0z"></path>
  </g>
</svg>
```

Replace with (design system §04 "Favicon / app tile" spec: dark rounded-square background, lighter gradient chevron):

```svg
<svg width="64" height="64" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Arctellis">
  <title>Arctellis</title>
  <defs>
    <linearGradient id="arctellisFavicon" x1="50" y1="0" x2="50" y2="100" gradientUnits="userSpaceOnUse">
      <stop stop-color="#5FBDF2"/>
      <stop offset="1" stop-color="#34A6EB"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="100" height="100" rx="20" fill="#14323D"/>
  <path transform="translate(50,50) scale(0.42) translate(-50,-50)" d="M50 6 L93 94 L50 71 L7 94 Z" fill="url(#arctellisFavicon)"/>
</svg>
```

- [ ] **Step 2: Remove the stale binary favicon**

Run:

```bash
git rm apps/frontend/src/app/favicon.ico
```

- [ ] **Step 3: Start the dev server and confirm the favicon**

Run: `cd apps/frontend && npm run dev`
Open `http://localhost:3000` in a browser and check the browser tab icon shows the new dark tile with the azure/teal chevron (may require a hard refresh / cache clear to see the change). Stop the server (Ctrl+C).

- [ ] **Step 4: Run the full test suite one last time**

Run: `cd apps/frontend && npm test`
Expected: all existing suites pass.

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/src/app/icon.svg
git commit -m "feat(frontend): replace favicon with Arctellis chevron mark (FE-15)"
```

---

### Task 9: Final manual verification pass

**Files:** none (verification only).

- [ ] **Step 1: Run the full automated suite once more**

Run: `cd apps/frontend && npm test && npm run lint`
Expected: all tests pass, no lint errors.

- [ ] **Step 2: Manual visual walkthrough**

Run: `cd apps/frontend && npm run dev`, open `http://localhost:3000`, and check each item against the spec's verification list:

1. `ChatHeader` in the empty-state view (Arctellis lockup, no "New conversation" button)
2. Empty-state hero: chevron icon, heading, subtext with no em dash, suggestion input focus ring (azure, not gold)
3. Send a message — confirm: composer button turns azure when text is entered; typing indicator dots are azure while streaming; header now shows the "New conversation" button
4. Ask a question that returns a markdown table with a status column and a currency/date column — confirm status badges and numeric/date cells render in JetBrains Mono
5. Ask a question that returns prose with inline code or a blockquote (if easily reproducible) — confirm teal/surface-2 styling, not blue
6. Check the browser tab favicon shows the new chevron tile

- [ ] **Step 3: Stop the dev server**

Press Ctrl+C in the terminal running `npm run dev`.

- [ ] **Step 4: Update the brain — mark FE-15 done and log a daily note**

Per `CLAUDE.md`, after a story is completed:

1. Edit `brain/stories/frontend/FE-15 Adopt Arctellis Design System.md` — change frontmatter `tag: todo` to `tag: done`.
2. Edit `brain/stories/frontend/Story Board - Frontend.md` — change the FE-15 row's status from `` `todo` `` to `` `done` ``.
3. Create `brain/stories/daily-updates/2026-07-14.md` (or append if it already exists for today) with:

```markdown
- Completed [FE-15] Adopt Arctellis Design System — remapped globals.css to the Arctellis teal/azure palette via a two-layer token system (brand tokens + shadcn semantic aliases), swapped Geist for Hanken Grotesk + JetBrains Mono, replaced the header logo and hero icon/favicon with the Arctellis lockup and chevron mark, and recoloured the composer/typing-indicator live-signal accents and markdown code/blockquote styling from the old SharePoint-blue/RTP-gold tokens.
```

- [ ] **Step 5: Commit the brain updates**

```bash
git add "brain/stories/frontend/FE-15 Adopt Arctellis Design System.md" "brain/stories/frontend/Story Board - Frontend.md" "brain/stories/daily-updates/2026-07-14.md"
git commit -m "chore(brain): mark FE-15 done"
```
