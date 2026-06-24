---
title: Backend Story Board
tag: active
component: backend
created: 2026-06-04
---
x
# Backend Story Board — SharePoint List AI Assistant

FastAPI + LangChain + Microsoft Graph backend. Stories derived from the [[PRD-SharePoint-List-AI-Assistant|PRD]] and [[Architecture-SharePoint-List-AI-Assistant|Architecture]] docs.

**Stack:** Python FastAPI · LangChain · Azure OpenAI · Microsoft Graph (`msgraph-sdk`) · Entra ID · Azure Key Vault · Azure Container Apps. Lives in a shared **monorepo** with the frontend.

> Status is tracked per story in frontmatter `tag`: `todo` · `in-progress` · `review` · `done`.

## Stories

| ID    | Story                                              | Phase          | Status |
| ----- | -------------------------------------------------- | -------------- | ------ |
| BE-00 | [[BE-00 Monorepo and Backend Project Setup]]       | 1 — Foundation | `done` |
| BE-01 | [[BE-01 Entra App Registration and Graph Auth]]    | 1 — Foundation | `done` |
| BE-02 | [[BE-02 SharePoint Service Read Items and Schema]] | 1 — Foundation | `done` |
| BE-03 | [[BE-03 SharePoint Data Caching]]                  | 1 — Foundation | `done` |
| BE-04 | [[BE-04 List Data Tools]]                          | 2 — Agent core | `done` |
| BE-05 | [[BE-05 LangChain Agent and Azure OpenAI]]         | 2 — Agent core | `done` |
| BE-06 | [[BE-06 Conversation Endpoint with SSE Streaming]] | 2 — Agent core | `done` |
| BE-07 | [[BE-07 Entra Token Validation Middleware]]        | 2 — Agent core | `done` |
| BE-08 | [[BE-08 Large-List Filtered Retrieval]]            | 4 — Hardening  | `done` |
| BE-09 | [[BE-09 Clarification and Out-of-Scope Handling]]  | 4 — Hardening  | `done` |
| BE-10 | [[BE-10 Observability Logging]]                    | 4 — Hardening  | `done` |
| BE-11 | [[BE-11 Accuracy Test Suite]]                      | 4 — Hardening  | `done` |
| BE-12 | [[BE-12 Key Vault Secrets and Deployment]]         | 5 — Deploy     | `todo` |
| BE-13 | [[BE-13 Migrate LLM Provider to Azure OpenAI]]     | 5 — Deploy     | `done` |
| BE-14 | [[BE-14 M365 Group Membership Check]]              | 6 — Access Control | `todo` |

## Phase grouping

- **Phase 1 — Foundation:** BE-00, BE-01, BE-02, BE-03
- **Phase 2 — Agent core:** BE-04, BE-05, BE-06, BE-07
- **Phase 4 — Hardening:** BE-08, BE-09, BE-10, BE-11
- **Phase 5 — Deploy:** BE-12, BE-13
- **Phase 6 — Access Control:** BE-14