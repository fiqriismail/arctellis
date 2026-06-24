---
title: Frontend Story Board
tag: active
component: front-end
created: 2026-06-04
---
# Frontend Story Board — SharePoint List AI Assistant

Next.js + shadcn/ui chat client. Stories derived from the [[PRD-SharePoint-List-AI-Assistant|PRD]] and [[Architecture-SharePoint-List-AI-Assistant|Architecture]] docs.

**Stack:** Next.js (App Router) · shadcn/ui (light theme) · SSE streaming · Entra ID sign-in · Azure Static Web Apps. Pure client of the backend — holds no secrets. Lives in a shared **monorepo** with the backend.

> Status is tracked per story in frontmatter `tag`: `todo` · `in-progress` · `review` · `done`.

## Stories

| ID    | Story                                                       | Phase       | Status |
| ----- | ----------------------------------------------------------- | ----------- | ------ |
| FE-00 | [[FE-00 Monorepo and Frontend Project Setup]]               | 3 — Chat UI | `done` |
| FE-01 | [[FE-01 Chat Layout and Centred Input]]                     | 3 — Chat UI | `done` |
| FE-02 | [[FE-02 Conversation Thread]]                               | 3 — Chat UI | `done` |
| FE-03 | [[FE-03 Markdown Answer Rendering]]                         | 3 — Chat UI | `done` |
| FE-04 | [[FE-04 SSE Streaming and Loading Indicator]]               | 3 — Chat UI | `done` |
| FE-05 | [[FE-05 Session Conversation History]]                      | 3 — Chat UI | `done` |
| FE-06 | [[FE-06 New Conversation Control]]                          | 3 — Chat UI | `done` |
| FE-07 | [[FE-07 Entra Sign-in and Auth Gate]]                       | 3 — Chat UI | `done` |
| FE-08 | [[FE-08 Backend API Client]]                                | 3 — Chat UI | `done` |
| FE-09 | [[FE-09 Deploy to Azure Static Web Apps]]                   | 5 — Deploy  | `done` |
| FE-10 | [[FE-10 Migrate Inline Styles to shadcn UI]]                | 3 — Chat UI | `todo` |
| FE-11 | [[FE-11 Styled Table Rendering with Status Badges]]         | 3 — Chat UI | `done` |
| FE-12 | [[FE-12 Chart View for Assistant Tables]]                   | 3 — Chat UI | `done` |
| FE-13 | [[FE-13 Sortable Tables with Currency and Date Formatting]] | 3 — Chat UI | `done` |
| FE-14 | [[FE-14 M365 Group Access Gate]]                           | 6 — Access Control | `todo` |

## Phase grouping

- **Phase 3 — Chat UI:** FE-00, FE-01, FE-02, FE-03, FE-04, FE-05, FE-06, FE-07, FE-08, FE-12, FE-13
- **Phase 5 — Deploy:** FE-09
- **Phase 6 — Tech Debt:** FE-10
- **Phase 6 — Access Control:** FE-14

