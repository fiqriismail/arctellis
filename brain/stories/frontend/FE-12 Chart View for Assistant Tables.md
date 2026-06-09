---
title: FE-12 Chart View for Assistant Tables
tag: done
component: front-end
created: 2026-06-07
---
# FE-12 Chart View for Assistant Tables

Add a **Table / Chart** toggle to the assistant's Markdown tables so users can
visualise tabular answers as a **bar**, **pie**, or **donut** chart. Pure
frontend feature — the chart is built by parsing the table the agent already
returns. No backend or agent changes.

Builds on [[FE-11 Styled Table Rendering with Status Badges]].

## Acceptance Criteria

- Uses the shadcn `Chart` component (Recharts); light theme, CSS-variable colours, no hard-coded hex.
- A table that has at least one label (text) column **and** one numeric column shows a Table / Chart toggle; non-chartable tables render unchanged with no toggle.
- Chart-type selector offers **Bar** (default), **Pie**, and **Donut**.
- Category labels default to the first text column; values default to the first numeric column. When multiple numeric columns exist, a dropdown lets the user choose the value column.
- Numeric inference tolerates thousands separators and a leading currency symbol; a column is treated as numeric only when the majority of its non-empty cells parse as numbers.
- Pie/donut group a long tail of categories into "Other" and drop non-positive slices; bar handles many categories and negative values.
- Table parsing lives in a pure, unit-tested helper (`lib/parseMarkdownTable.ts`); chart rendering and the toggle are separate components in the chat feature slice.
- All existing `MarkdownContent` tests remain green; new tests cover the parser, toggle visibility, and chart rendering (TDD).

## Notes

- Vertical slice under `src/features/chat`: `lib/parseMarkdownTable.ts`, `components/ChartView.tsx`, `components/TableChartToggle.tsx`, wired into `components/MarkdownContent.tsx`.
- Out of scope (deferred): line/area charts, backend-emitted chart specs, persisting the chosen view across messages, chart export, multi-series grouped bars.
- Design spec: `docs/superpowers/specs/2026-06-07-fe12-chart-view-design.md`.

## Dependencies
- [[FE-11 Styled Table Rendering with Status Badges]]


## PR
[#33](https://github.com/arctellis/group-one-rtp/pull/33) — open. Note: chart toggle is offered only for two-column aggregations (wider tables render table-only). Bundled with FE-13 + RTP rebrand on branch feature/FE-12-chart-view.