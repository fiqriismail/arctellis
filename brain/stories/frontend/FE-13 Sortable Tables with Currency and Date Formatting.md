---
title: FE-13 Sortable Tables with Currency and Date Formatting
tag: done
component: front-end
created: 2026-06-07
---
# FE-13 Sortable Tables with Currency and Date Formatting

Make assistant tables interactive and consistently formatted by default:
client-side column sorting, money columns shown as currency, dates as
dd-mm-yyyy. Builds on [[FE-12 Chart View for Assistant Tables]] (reuses the
same parsed-table data).

## Acceptance Criteria

- Clicking a column header sorts the rows; clicking again reverses. Numeric and
  currency columns sort numerically, date columns chronologically, text columns
  alphabetically. A sort indicator shows the active column/direction.
- Money-named columns (header contains amount, cost, price, total, budget,
  estimate, value, sum, fee, …) render as currency with **two decimals**,
  **right-aligned**, defaulting to **€ (EUR)**.
- If a cell already carries an explicit currency symbol (e.g. `$1,000`), that
  currency is preserved; only bare numbers default to €.
- Non-money numeric columns are right-aligned but not currency-formatted.
- Date columns render as **dd-mm-yyyy**.
- Known status values still render as coloured badges ([[FE-11 Styled Table Rendering with Status Badges]]).
- Defaults apply to every assistant table with no prompt/backend changes.
- Pure, unit-tested helpers; all existing table/chart tests stay green (TDD).

## Notes

- Vertical slice under `src/features/chat`: `lib/formatCell.ts` (parse/format +
  column-kind helpers), `components/DataTable.tsx` (sortable, formatted table),
  wired into `components/MarkdownContent.tsx`. Column kinds
  (currency/number/date/text) are inferred in `lib/parseMarkdownTable.ts`.
- The table is now rendered from parsed cell data rather than the raw Markdown
  DOM, which is what enables sorting and consistent formatting.
- Currency uses `€` by default; explicit symbols in the data win — honouring
  "Euros unless somebody explicitly asks to change".
- Implemented alongside FE-12 on `feature/FE-12-chart-view`.

## Dependencies
- [[FE-12 Chart View for Assistant Tables]]
- [[FE-11 Styled Table Rendering with Status Badges]]


## PR
[#33](https://github.com/arctellis/group-one-rtp/pull/33) — open (bundled with FE-12 + RTP rebrand).