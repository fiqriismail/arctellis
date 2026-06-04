# Product Requirements Document — SharePoint List AI Assistant

| | |
|---|---|
| **Version** | 0.2 (Draft) |
| **Date** | 4 June 2026 |
| **Author** | Fiqri |
| **Status** | For review |
| **Change note** | Technology stack revised from Blazor Server / Semantic Kernel to Next.js (frontend) + Python FastAPI (backend) + LangChain. LLM (Azure OpenAI) and data access (Microsoft Graph / Entra ID) unchanged. |

---

## 1. Overview

The SharePoint List AI Assistant is a web application that lets users ask questions about the data in a SharePoint list using plain English. Instead of building filters, views, or exporting to Excel, a user types a question into a chat box ("how many items are approved?", "what's the total budget for the Marketing department?") and receives a written answer with the relevant numbers and summaries.

The application is a Next.js web frontend backed by a Python FastAPI service and Azure OpenAI. An LLM interprets the user's question and decides which data operations to run; the backend executes those operations deterministically against the SharePoint list via Microsoft Graph. This split keeps natural-language flexibility while guaranteeing that calculations are accurate.

## 2. Problem Statement

SharePoint lists are easy to populate but awkward to interrogate. Answering a question like "what was the average value of closed items last quarter" requires either building a view, using a calculated column, or exporting the data. Non-technical stakeholders often cannot do this themselves and depend on a developer or analyst. There is no fast, conversational way to get summaries and ad-hoc calculations from list data.

## 3. Goals and Non-Goals

### 3.1 Goals
- Let a user ask a free-text question and get a correct, readable answer about the list data.
- Support aggregations: counts, sums, averages, min/max, group-by, and filtered subsets.
- Guarantee numerical accuracy — arithmetic is performed in code, never left to the LLM.
- Provide a clean, minimal chat interface modelled on a modern AI assistant client.
- Keep all credentials and data access server-side.

### 3.2 Non-Goals (for v1)
- Writing back to or modifying the SharePoint list.
- Supporting multiple lists or cross-list joins.
- User-level row security or per-user data filtering.
- Document/attachment content analysis within list items.
- Mobile-native applications.

## 4. Target Users and Use Cases

**Primary users:** Internal team members who need information from a SharePoint list but are not comfortable building views or formulas — managers, coordinators, analysts.

**Representative use cases:**
- "How many items have status = Approved?"
- "What is the total of the Budget column?"
- "Average completion time for items closed this year."
- "Which department has the most open requests?"
- "Summarise the items created in the last 30 days."

## 5. Functional Requirements

### 5.1 Chat Interface
- **FR-1** A single, centred text input is the primary control. No filter panels, dropdowns, or form fields. Built with Next.js and shadcn/ui components (light theme).
- **FR-2** Submitted questions and returned answers appear as a vertical conversation thread (user message, then assistant answer).
- **FR-3** Assistant answers render formatted text (markdown) so numbers, lists, and short tables display cleanly.
- **FR-4** While an answer is being generated, a loading/typing indicator is shown. Streaming the response token-by-token is preferred.
- **FR-5** Conversation history is retained for the duration of the browser session so follow-up questions ("and how about last month?") have context.
- **FR-6** A way to start a new/empty conversation.

### 5.2 Query and Answer Engine
- **FR-7** The LLM must decide which data operation(s) answer the question using function/tool calling — it does not perform calculations itself.
- **FR-8** The system exposes, at minimum, these operations to the LLM: retrieve filtered rows, count rows by condition, sum a column, average a column, group-and-aggregate by a column, and return list schema/column names.
- **FR-9** All numeric computation is executed in application code against retrieved data.
- **FR-10** If a question is ambiguous or references a column that does not exist, the assistant asks a clarifying question rather than guessing.
- **FR-11** If a question is unrelated to the list data, the assistant says so politely instead of fabricating an answer.

### 5.3 SharePoint Data Access
- **FR-12** The application reads list items through the Microsoft Graph API.
- **FR-13** The list site and list ID are configuration values, not hard-coded.
- **FR-14** The application can return the list's column names and types so the LLM knows what it can query.
- **FR-15** Retrieved list data is cached briefly (target 30–60 seconds) so a single question that triggers several operations does not re-fetch repeatedly.

## 6. Technical Architecture

### 6.1 Stack
- **Frontend:** Next.js (App Router) with shadcn/ui components (light theme), hosted on **Azure Static Web Apps**. A pure client of the backend; it holds no secrets and makes no direct Graph or LLM calls.
- **Backend / host:** Python FastAPI service, packaged as a container and deployed as a **container-based application** (e.g. Azure Container Apps). Holds all AI orchestration, Graph access, and secrets server-side, and streams answers to the frontend.
- **AI orchestration:** LangChain (agent with tool calling). LangChain tools are the boundary where the LLM's intent becomes deterministic Python code.
- **LLM:** Azure OpenAI (chat completion deployment with function-/tool-calling support), accessed via `langchain-openai`'s `AzureChatOpenAI`.
- **Data access:** Microsoft Graph SDK for Python (`msgraph-sdk`), authenticated via `azure-identity` / `msal`.
- **Identity:** Microsoft Entra ID app registration.

### 6.2 Component Layers
1. **Next.js chat component** — renders the conversation, captures input, displays streamed answers. Calls the backend over HTTP and consumes a streamed (SSE) response.
2. **FastAPI conversation endpoint** — holds chat history per session, invokes the LangChain agent, and streams tokens back to the frontend.
3. **LangChain agent + Azure OpenAI** — interprets questions and selects which tools to call.
4. **List Data tools** — a set of LangChain tools (count, sum, average, group-by, filter, get-schema). This is the boundary where the LLM's intent becomes deterministic Python code.
5. **SharePoint service** — Python module wrapping Graph calls, handling auth and caching.
6. **SharePoint Online** — the source list.

Request flow: user question → Next.js → FastAPI conversation endpoint → LangChain agent (Azure OpenAI) decides on tool calls → List Data tools execute them against cached list data → results returned to the model → model composes a natural-language answer → streamed (SSE) back through FastAPI to the Next.js UI.

### 6.3 Tool/Function Design Principle
The LLM is responsible only for *understanding the question* and *phrasing the answer*. Every fact and figure in the answer originates from code execution. LangChain tool names, descriptions, and argument schemas must be written carefully, since the model relies on them to choose correctly.

### 6.4 Authentication
- The app registration is granted Graph application permission `Sites.Read.All` (or the more scoped `Sites.Selected` if the list's site can be explicitly granted), with admin consent.
- Client-credentials flow (via `azure-identity` / `msal` in the FastAPI backend) is used for an app that reads data on its own behalf. If per-user identity is later required, this moves to delegated/on-behalf-of auth — see Open Questions.
- The Next.js frontend never holds Graph or Azure OpenAI credentials. The Next.js ↔ FastAPI boundary is the trust boundary.
- End-user access is gated by Entra ID sign-in: users authenticate in the Next.js app, and the FastAPI backend validates the resulting token on every request and rejects unauthenticated calls (NFR-8). This end-user sign-in is distinct from the app's own client-credentials identity used to read SharePoint — in v1 all authenticated users share that single read identity (per-user SharePoint permissions remain Open Question 1).

## 7. Non-Functional Requirements

### 7.1 Security
- **NFR-1** All API keys, secrets, and sensitive connection settings (Azure OpenAI keys, the Entra client secret, etc.) are stored in **Azure Key Vault** and retrieved by the backend at runtime — never in the Next.js client code or source control. The container's managed identity is granted read access to the vault; local development may use environment variables / `.env` standing in for the vault, but no secret is ever committed.
- **NFR-2** No list data or credentials are exposed to the browser beyond the rendered answer text. Secrets and Graph calls stay inside the FastAPI backend.
- **NFR-8** The system is accessible only to authenticated members of the organisation — no anonymous access. End users sign in with Entra ID; both the Next.js frontend and the FastAPI backend require a valid authenticated session, and the backend rejects unauthenticated requests. (User sign-in governs *access to the app*; it is separate from how the app reads SharePoint data, which remains the app's own client-credentials identity in v1 — see §6.4 and Open Question 1.)

### 7.2 Performance
- **NFR-3** Target end-to-end response time under ~5 seconds for a typical question on a list of moderate size.
- **NFR-4** List data caching prevents redundant Graph calls within a single multi-step answer.

### 7.3 Accuracy and Reliability
- **NFR-5** Numeric answers must match what a direct calculation on the list would produce — verified by test cases.
- **NFR-6** The assistant must not invent column names, values, or figures.

### 7.4 Observability
- **NFR-7** Log each question, the functions the model chose to call with their arguments, and the final answer, to support debugging and trust verification.

## 8. Data Considerations

- **Large lists:** Fetching every row will eventually exceed the LLM context window and slow responses. The filtered-retrieval function should push filtering to Graph (`$filter`) so only relevant rows are loaded. A row-count threshold should trigger filtered-only behaviour.
- **Column typing:** SharePoint returns field values loosely typed. The data layer must safely parse numbers, dates, and choice fields, and ignore rows where a value cannot be parsed for a given operation.
- **Field naming:** Internal field names can differ from display names. The schema function should expose names the model can reliably reference.

## 9. Out of Scope for v1

Write-back, multi-list support, per-user row security, attachment/document analysis, scheduled reports or alerts, and authentication of end users against their own SharePoint permissions. These are candidates for later phases.

## 10. Milestones / Phasing

| Phase | Scope |
|---|---|
| **Phase 1 — Foundation** | Entra app registration, Graph access, Python SharePoint service reads list items and schema. Verified with a script/test harness. |
| **Phase 2 — Agent core** | LangChain agent + Azure OpenAI wired up in FastAPI. List Data tools with count, sum, average, group-by, filter, schema. Tool calling working end-to-end. |
| **Phase 3 — Chat UI** | Next.js + shadcn/ui chat: single input, conversation thread, markdown rendering, loading indicator, SSE streaming, new-conversation control. |
| **Phase 4 — Hardening** | Caching, large-list filtered retrieval, logging, ambiguity/clarification handling, accuracy test suite. |
| **Phase 5 — Deploy** | Secrets in Azure Key Vault (read via the container's managed identity). Frontend deployed to Azure Static Web Apps; backend container deployed as a container app. Smoke testing. |

## 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| LLM performs arithmetic itself and produces wrong numbers. | All computation in code; the model only phrases results. Accuracy test suite. |
| Large list overflows context window. | Filtered retrieval pushed to Graph; threshold-based behaviour. |
| Model calls the wrong function or misreads a column. | Carefully written function/parameter descriptions; schema function; clarification behaviour. |
| Graph permissions over-broad. | Prefer `Sites.Selected` scoped to the one site. |
| Cost of frequent Azure OpenAI calls. | Caching, concise prompts, monitor token usage. |

## 12. Decisions

These decisions were captured during review and resolve the questions that were previously open.

| # | Decision | Rationale / notes |
|---|---|---|
| **D-1 — Data identity** | Single shared read account for v1; the list is read via the backend's own client-credentials identity (§6.4). | The SharePoint site/list is shared with a group whose members all have the same access, so there are no per-user/per-item distinctions to honour. *Constraint:* the users allowed to sign in to the app should match the SharePoint members group. Per-user (delegated/OBO) auth is a later-phase option if item-level security is ever introduced. |
| **D-2 — Access control** | Authenticated organisation members only; no anonymous access (Entra ID sign-in). | See NFR-8. |
| **D-3 — Cache window** | Keep the 30–60s cache window; TTL is a configuration value. | Avoids re-fetching within a single multi-step answer while keeping data near-real-time (FR-15 / NFR-4); configurable so it can be tuned without a code change. |
| **D-4 — Target list** | A specific list is chosen; concrete details to be confirmed (see below). | Design stays list-agnostic and discovers structure at runtime via the get-schema tool; list site/ID are configuration (FR-13), not hard-coded. |
| **D-5 — Hosting & secrets** | Frontend on Azure Static Web Apps; backend as a container-based app (e.g. Azure Container Apps); secrets in Azure Key Vault. | See §6.1 and NFR-1. |

### Still to confirm — target list details (D-4)

| Field | Value |
|---|---|
| Site URL | _TBC_ |
| List name | _TBC_ |
| List ID | _TBC_ |
| Key columns (name → type) | _TBC_ |
| Approx. row count | _TBC_ |
| Filtered-retrieval row threshold | _TBC (see §8)_ |

## 13. Success Metrics

- A defined set of representative questions returns answers that match manually verified results (target: 100% numeric accuracy on the test set).
- Median response time within the performance target.
- Pilot users can answer their own list questions without developer involvement.
