---
id: BE-06
title: FastAPI Conversation Endpoint + SSE Streaming
tag: done
epic: Agent Core
phase: Phase 2 — Agent core
prd_refs:
  - FR-4
  - FR-5
  - §6.2
arch_refs:
  - §3.2
  - §4
created: 2026-06-04
---

# BE-06 — FastAPI Conversation Endpoint + SSE Streaming

## Story
As the frontend, I want a conversation endpoint that holds per-session chat history, invokes the agent, and streams the answer back so that the UI can render answers token-by-token.

## Context
The conversation endpoint is the trust-boundary entry point (Architecture §3.2). It relays the agent's output as a Server-Sent Events stream (§4).

## Acceptance Criteria
- [ ] `POST /chat` (or equivalent) accepts a question + session identifier.
- [ ] Per-session chat history maintained so follow-ups have context (FR-5).
- [ ] Endpoint invokes the LangChain agent and **streams tokens via SSE** (FR-4).
- [ ] Streaming verified end-to-end with a client consuming the SSE response.
- [ ] Errors surface cleanly to the client without leaking secrets or internals.

## Dependencies
- [[BE-05 LangChain Agent and Azure OpenAI]]
- [[BE-07 Entra Token Validation Middleware]]
