# FE-12 Chart View for Assistant Tables — Design Spec

**Date:** 2026-06-07
**Status:** Approved (pending plan)

## Goal

Let users visualise the tabular answers the assistant returns. When the assistant
streams a Markdown table, the frontend offers a **Table / Chart** toggle and can
render the parsed rows as a **bar**, **pie**, or **donut** chart. Pure frontend
feature — no backend or agent changes.

## Why

The agent already returns structured, comparative data as Markdown tables
(FE-11). A chart makes proportions and comparisons (e.g. items by status, count
by department) easier to read at a glance, with no extra round-trips.

## Approach

Parse the already-rendered table on the client and render a chart from it. This
was chosen over a backend chart-spec format (no agent/prompt changes, works with
everything the agent already emits) and over a manual column-mapping builder
(too much UI for v1).

## Library

shadcn `Chart` component (`npx shadcn add chart`), which wraps **Recharts**.
Keeps us on shadcn + the light theme + CSS-variable tokens per project
convention. Recharts is the only new runtime dependency.

## Architecture (vertical slice — all under `src/features/chat`)

| Unit | Responsibility | Depends on |
|---|---|---|
| `lib/parseMarkdownTable.ts` | Pure function: `(headerCells, rowCells) → { columns, rows }`, inferring which columns are numeric. No React. | nothing |
| `components/ChartView.tsx` | Render a shadcn bar/pie/donut from parsed `{ columns, rows }`. | shadcn chart, parsed data |
| `components/TableChartToggle.tsx` | Toolbar with Table / Chart switch + chart-type selector; hosts either the original table or `ChartView`. | `ChartView` |
| `components/MarkdownContent.tsx` (modify) | Wrap each chartable table in `TableChartToggle`. | toggle |

### Data flow

1. `MarkdownContent`'s `table` renderer receives the table's React children
   (thead/tbody). It extracts the header labels and row cell text.
2. `parseMarkdownTable` converts those into `{ columns: {name, numeric}[], rows: string[][] }`.
3. A table is **chartable** when it has ≥1 non-numeric (label) column **and** ≥1
   numeric (value) column. If not chartable, render the table exactly as today —
   no toggle shown.
4. When chartable, render the `TableChartToggle`: default view is the original
   styled table; switching to **Chart** shows `ChartView`.

### Chart configuration (defaults, with light overrides)

- **Category (labels):** first non-numeric column.
- **Value:** first numeric column. If multiple numeric columns exist, a small
  dropdown lets the user pick which one (bar can also show all numeric columns as
  grouped series — but v1 keeps it to one selected value column for simplicity).
- **Chart type selector:** Bar (default) · Pie · Donut. Donut = pie with an inner
  radius.
- Colours come from shadcn chart CSS variables (`--chart-1..5`), no hard-coded hex.

## Edge cases

- **No numeric column** → not chartable → no toggle (current behaviour).
- **Many categories** (> ~8): bar stays readable; pie/donut groups the long tail
  into an "Other" slice to avoid an unreadable wheel.
- **Non-numeric / blank cells in a value column**: coerced to 0 for charting; the
  parser already flags a column numeric only when the majority of its non-empty
  cells parse as numbers.
- **Negative / zero values**: allowed for bar; pie/donut ignore non-positive
  slices (and note if any were dropped).
- **Currency / formatted numbers** (e.g. `1,234.50`, `£12`): the numeric parser
  strips thousands separators and a leading currency symbol before parsing.

## Testing (TDD)

- `parseMarkdownTable` unit tests: numeric inference, currency/comma stripping,
  non-chartable tables, empty/malformed input, majority-numeric rule.
- `TableChartToggle`: toggle hidden for non-chartable tables; visible and
  switches views for chartable ones.
- `ChartView`: renders given parsed data; respects chart-type selection; honours
  the value-column dropdown.
- All existing `MarkdownContent` tests stay green.

## Scope / YAGNI (v1)

**In:** bar, pie, donut; auto column detection with a value-column dropdown;
client-side parsing only.

**Out (deferred):** line/area charts; backend chart specs; persisting the
chosen view/type across messages; exporting/downloading charts; multi-series
grouped bars beyond the single selected value column.

## Components / boundaries check

- `parseMarkdownTable` is pure and testable with no React — the riskiest logic is
  isolated.
- `ChartView` only knows about parsed data, not Markdown.
- `TableChartToggle` only orchestrates view state.
- `MarkdownContent` only decides chartability and delegates.
