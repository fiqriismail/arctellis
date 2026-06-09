---
id: FE-08
title: Backend API Client (HTTP + SSE)
tag: done
epic: Chat UI
phase: Phase 3 — Chat UI
prd_refs:
  - §6.2
  - NFR-1
  - NFR-2
arch_refs:
  - §3.1
  - §6.1
created: 2026-06-04
---

# FE-08 — Backend API Client (HTTP + SSE)

## Story
As the frontend, I want a typed client for the backend conversation endpoint so that the UI can send questions and consume the streamed answer cleanly.

## Context
The frontend is a pure client of the backend over HTTP, consuming a streamed SSE response (Architecture §3.1, §6.1). Its only backend is the FastAPI conversation endpoint — no direct Graph/LLM calls (NFR-1, NFR-2).

## Acceptance Criteria
- [ ] Client posts question + session id to the conversation endpoint and consumes the **SSE** stream.
- [ ] Bearer token from [[FE-07 Entra Sign-in and Auth Gate]] attached to requests.
- [ ] Makes **no direct Graph or Azure OpenAI calls** (NFR-1, NFR-2).
- [ ] Typed request/response contracts; errors and non-200s surfaced to the UI.
- [ ] Backend base URL from environment config.

## Dependencies
- [[FE-00 Monorepo and Frontend Project Setup]]
- Backend: [[BE-06 Conversation Endpoint with SSE Streaming]]
