---
id: FE-04
title: SSE Streaming & Loading Indicator
tag: done
epic: Chat UI
phase: Phase 3 — Chat UI
prd_refs:
  - FR-4
arch_refs:
  - §3.1
  - §4
created: 2026-06-04
---

# FE-04 — SSE Streaming & Loading Indicator

## Story
As a user, I want the answer to stream in token-by-token with a typing indicator while it generates so that the app feels responsive.

## Context
The frontend consumes a streamed (SSE) response and appends tokens as they arrive; a loading/typing indicator shows while generating (PRD FR-4; Architecture §3.1, §4).

## Acceptance Criteria
- [ ] Frontend consumes the backend **SSE** stream and appends tokens as they arrive (FR-4).
- [ ] A loading/typing indicator is shown while an answer is being generated (FR-4).
- [ ] Indicator clears when the stream completes.
- [ ] Stream interruptions/errors handled gracefully (partial answer + error state).

## Dependencies
- [[FE-08 Backend API Client]]
- [[FE-03 Markdown Answer Rendering]]
- Backend: [[BE-06 Conversation Endpoint with SSE Streaming]]
