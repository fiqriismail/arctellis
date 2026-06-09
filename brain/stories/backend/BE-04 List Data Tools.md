---
id: BE-04
title: List Data Tools (count/sum/avg/group-by/filter/schema)
tag: done
epic: Agent Core
phase: Phase 2 — Agent core
prd_refs:
  - FR-7
  - FR-8
  - FR-9
  - NFR-5
  - NFR-6
  - §6.3
arch_refs:
  - §3.4
created: 2026-06-04
---

# BE-04 — List Data Tools

## Story
As the agent, I want a set of deterministic List Data tools so that every fact and figure in an answer originates from code, never from the LLM's own arithmetic.

## Context
This is the boundary where LLM intent becomes deterministic Python (Architecture §3.4). Tool names, descriptions, and argument schemas must be written carefully — the model relies on them to choose correctly (§6.3).

## Acceptance Criteria
- [ ] LangChain tools implemented for the minimum set (FR-8):
  - [ ] `get_schema` — list column names/types (FR-14)
  - [ ] `filter_rows` — retrieve filtered rows
  - [ ] `count_rows` — count by condition
  - [ ] `sum_column` — sum a numeric column
  - [ ] `average_column` — average a numeric column
  - [ ] `group_and_aggregate` — group-by + aggregate
- [ ] **All numeric computation runs in Python** over retrieved data (FR-9, NFR-5); the model never computes (FR-7).
- [ ] Tools parse loosely-typed values and skip rows that cannot be parsed for a given operation (§8).
- [ ] Tool names/descriptions/arg schemas are clear and unambiguous (§6.3).
- [ ] Tools never invent column names or values (NFR-6).

## Dependencies
- [[BE-02 SharePoint Service Read Items and Schema]]
- [[BE-03 SharePoint Data Caching]]
