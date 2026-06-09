---
id: BE-08
title: Large-List Filtered Retrieval
tag: done
epic: Hardening
phase: Phase 4 — Hardening
prd_refs:
  - §8
arch_refs:
  - §5.2
created: 2026-06-04
---

# BE-08 — Large-List Filtered Retrieval

## Story
As the backend, I want filtering pushed to Graph and a row-count threshold for large lists so that fetching data never overflows the LLM context window or slows responses.

## Context
Fetching every row eventually overflows context (PRD §8). The filtered-retrieval path pushes `$filter` to Graph and a threshold triggers filtered-only behaviour (Architecture §5.2).

## Acceptance Criteria
- [ ] `filter_rows` pushes filtering to Graph via `$filter` so only relevant rows load (§8).
- [ ] A **configurable row-count threshold** triggers filtered-only behaviour (D-4 "Filtered-retrieval row threshold").
- [ ] Behaviour verified against a large (or simulated large) list — no full-list fetch beyond threshold.
- [ ] Threshold is configuration, not hard-coded.

## Dependencies
- [[BE-04 List Data Tools]]
