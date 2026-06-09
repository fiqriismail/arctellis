---
id: BE-10
title: Observability Logging
tag: done
epic: Hardening
phase: Phase 4 — Hardening
prd_refs:
  - NFR-7
arch_refs:
  - §8
created: 2026-06-04
---

# BE-10 — Observability Logging

## Story
As an operator, I want each question, the tool calls the model chose (with arguments), and the final answer logged so that I can debug behaviour and verify that figures came from tool execution.

## Context
Logging supports debugging and trust verification (Architecture §8, NFR-7) — confirming answers are grounded in tool execution, not model invention.

## Acceptance Criteria
- [ ] Each request logs: the user's question, every tool call **with its arguments**, and the final answer (NFR-7).
- [ ] Logs structured for querying/inspection.
- [ ] No secrets logged; sensitive values redacted.
- [ ] Azure OpenAI token usage observable to manage cost (PRD §11 risk).

## Dependencies
- [[BE-06 Conversation Endpoint with SSE Streaming]]
