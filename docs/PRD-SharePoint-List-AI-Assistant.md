# Product Requirements Document — SharePoint List AI Assistant

| | |
|---|---|
| **Version** | 0.1 (Draft) |
| **Date** | 24 May 2026 |
| **Author** | Fiqri |
| **Status** | For review |

---

## 1. Overview

The SharePoint List AI Assistant is a web application that lets users ask questions about the data in a SharePoint list using plain English. Instead of building filters, views, or exporting to Excel, a user types a question into a chat box ("how many items are approved?", "what's the total budget for the Marketing department?") and receives a written answer with the relevant numbers and summaries.

The application is a Blazor Server web app backed by Azure OpenAI. An LLM interprets the user's question and decides which data operations to run; the application code executes those operations deterministically against the SharePoint list via Microsoft Graph. This split keeps natural-language flexibility while guaranteeing that calculations are accurate.

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
- **FR-1** A single, centred text input is the primary control. No filter panels, dropdowns, or form fields.
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
- **Frontend / host:** Blazor Server (ASP.NET Core). Server-side rendering keeps secrets and Graph calls off the client.
- **AI orchestration:** Microsoft Semantic Kernel.
- **LLM:** Azure OpenAI (chat completion deployment with function-calling support).
- **Data access:** Microsoft Graph SDK (`Microsoft.Graph`), authenticated via `Azure.Identity`.
- **Identity:** Microsoft Entra ID app registration.

### 6.2 Component Layers
1. **Blazor chat component** — renders the conversation, captures input, displays streamed answers.
2. **Conversation service** — holds `ChatHistory` per session, calls the Kernel.
3. **Semantic Kernel + Azure OpenAI connector** — interprets questions and selects functions.
4. **List Data Plugin** — a set of `[KernelFunction]`-attributed methods (count, sum, average, group-by, filter, get-schema). This is the boundary where the LLM's intent becomes deterministic code.
5. **SharePoint service** — wraps Graph calls, handles auth and caching.
6. **SharePoint Online** — the source list.

Request flow: user question → Conversation service → Kernel (Azure OpenAI) decides on function calls → List Data Plugin executes them against cached list data → results returned to the model → model composes a natural-language answer → streamed back to the Blazor UI.

### 6.3 Tool/Function Design Principle
The LLM is responsible only for *understanding the question* and *phrasing the answer*. Every fact and figure in the answer originates from code execution. Function descriptions and parameter descriptions must be written carefully, since the model relies on them to choose correctly.

### 6.4 Authentication
- The app registration is granted Graph application permission `Sites.Read.All` (or the more scoped `Sites.Selected` if the list's site can be explicitly granted), with admin consent.
- Client-credentials flow is used for an app that reads data on its own behalf. If per-user identity is later required, this moves to delegated/on-behalf-of auth — see Open Questions.

## 7. Non-Functional Requirements

### 7.1 Security
- **NFR-1** Azure OpenAI keys, the Entra client secret, and all connection settings are stored in app configuration / a secret store (e.g. Azure Key Vault or user secrets in dev), never in client code or source control.
- **NFR-2** No list data or credentials are exposed to the browser beyond the rendered answer text.

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
| **Phase 1 — Foundation** | Entra app registration, Graph access, SharePoint service reads list items and schema. Verified with a console/test harness. |
| **Phase 2 — Agent core** | Semantic Kernel + Azure OpenAI wired up. List Data Plugin with count, sum, average, group-by, filter, schema functions. Function calling working end-to-end. |
| **Phase 3 — Chat UI** | Blazor chat component: single input, conversation thread, markdown rendering, loading indicator, streaming, new-conversation control. |
| **Phase 4 — Hardening** | Caching, large-list filtered retrieval, logging, ambiguity/clarification handling, accuracy test suite. |
| **Phase 5 — Deploy** | Configuration/secrets via Key Vault, deployment to Azure App Service, smoke testing. |

## 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| LLM performs arithmetic itself and produces wrong numbers. | All computation in code; the model only phrases results. Accuracy test suite. |
| Large list overflows context window. | Filtered retrieval pushed to Graph; threshold-based behaviour. |
| Model calls the wrong function or misreads a column. | Carefully written function/parameter descriptions; schema function; clarification behaviour. |
| Graph permissions over-broad. | Prefer `Sites.Selected` scoped to the one site. |
| Cost of frequent Azure OpenAI calls. | Caching, concise prompts, monitor token usage. |

## 12. Open Questions

1. Should answers reflect each end user's own SharePoint permissions, or is a single shared read account acceptable for v1? (This determines client-credentials vs. delegated auth.)
2. Does the app need to be accessible to anonymous users, or only authenticated members of the organisation?
3. How frequently does the list change — does the 30–60s cache window need tuning?
4. Is there a specific list already chosen, and what are its key columns and approximate row count?
5. Hosting target — Azure App Service, container, or other?

## 13. Success Metrics

- A defined set of representative questions returns answers that match manually verified results (target: 100% numeric accuracy on the test set).
- Median response time within the performance target.
- Pilot users can answer their own list questions without developer involvement.
