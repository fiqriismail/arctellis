---
id: BE-09
title: Clarification & Out-of-Scope Handling
tag: done
epic: Hardening
phase: Phase 4 — Hardening
prd_refs:
  - FR-10
  - FR-11
  - NFR-6
arch_refs:
  - §3.3
created: 2026-06-04
---

# BE-09 — Clarification & Out-of-Scope Handling

## Story
As a user, I want the assistant to ask for clarification when my question is ambiguous and to decline politely when my question is unrelated, so that I can trust it never fabricates answers.

## Context
Hardens the agent behaviour from [[BE-05 LangChain Agent and Azure OpenAI]] (Architecture §3.3). This is the formal pass to make clarification/decline reliable and tested.

## Acceptance Criteria
- [ ] Ambiguous questions or references to non-existent columns → assistant asks a clarifying question instead of guessing (FR-10).
- [ ] Questions unrelated to the list → assistant says so politely, no fabricated answer (FR-11).
- [ ] Assistant never invents column names, values, or figures (NFR-6).
- [ ] Behaviours covered by test cases / prompt-tuning evidence.

## Dependencies
- [[BE-05 LangChain Agent and Azure OpenAI]]
