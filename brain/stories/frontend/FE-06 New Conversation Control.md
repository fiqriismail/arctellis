---
id: FE-06
title: New Conversation Control
tag: done
epic: Chat UI
phase: Phase 3 — Chat UI
prd_refs:
  - FR-6
arch_refs:
  - §3.1
created: 2026-06-04
---

# FE-06 — New Conversation Control

## Story
As a user, I want a way to start a new, empty conversation so that I can ask an unrelated question without prior context bleeding in.

## Context
The UI offers a control to start a new/empty conversation (PRD FR-6).

## Acceptance Criteria
- [ ] A visible control starts a new/empty conversation (FR-6).
- [ ] Clears the visible thread and starts a fresh session context.
- [ ] Backend session context resets accordingly (new session id).
- [ ] Styled consistently with the shadcn light theme.

## Dependencies
- [[FE-05 Session Conversation History]]
