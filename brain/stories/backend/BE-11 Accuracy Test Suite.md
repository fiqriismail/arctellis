---
id: BE-11
title: Accuracy Test Suite
tag: done
epic: Hardening
phase: Phase 4 — Hardening
prd_refs:
  - NFR-5
  - §13
arch_refs:
  - §3.4
  - §10
created: 2026-06-04
---

# BE-11 — Accuracy Test Suite

## Story
As the team, I want an accuracy test suite over representative questions so that we can guarantee numeric answers match a direct calculation on the list.

## Context
Accuracy by construction is the headline architectural goal (Architecture §10, NFR-5). Success is measured by a defined set of questions returning manually-verified results (PRD §13).

## Acceptance Criteria
- [ ] A defined set of representative questions with manually-verified expected answers.
- [ ] Tests assert tool-computed numeric results **match direct calculation** on the list (NFR-5).
- [ ] Target: 100% numeric accuracy on the test set (PRD §13).
- [ ] Suite runnable in CI and as a regression guard.

## Dependencies
- [[BE-04 List Data Tools]]
- [[BE-05 LangChain Agent and Azure OpenAI]]
