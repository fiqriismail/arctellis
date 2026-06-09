---
title: FE-11 Styled Table Rendering with Status Badges
tag: done
component: front-end
created: 2026-06-06
---
# FE-11 Styled Table Rendering with Status Badges

Improve the Markdown table renderer in MarkdownContent to display styled tables with rounded corners matching shadcn/ui and coloured status badges for known status values.

## Acceptance Criteria

- Table has rounded corners and an outer border consistent with shadcn card styling
- Header row uses muted/subtle background instead of hard brand colour
- Even/odd row striping for readability
- Status cell values (e.g. Active, Inactive, Pending, Closed, Approved, Rejected) render as coloured badges
- Badge colours are semantic (green = active/approved, yellow = pending, red = inactive/rejected/closed)
- No hard-coded hex colours — uses CSS variable utility classes or shadcn tokens
- All existing MarkdownContent tests remain green

## Notes

- Status detection should be case-insensitive and limited to a known set to avoid false positives
- Wrap table in overflow-x container to handle narrow viewports