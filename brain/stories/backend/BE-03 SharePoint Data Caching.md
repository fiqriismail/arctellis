---
id: BE-03
title: SharePoint Data Caching
tag: done
epic: Foundation
phase: Phase 1 — Foundation
prd_refs:
  - FR-15
  - NFR-4
  - D-3
arch_refs:
  - §5.3
created: 2026-06-04
---

# BE-03 — SharePoint Data Caching

## Story
As the backend, I want retrieved list data cached briefly so that a single question triggering several operations does not re-fetch from Graph repeatedly.

## Context
A short-lived cache sits in the SharePoint service (Architecture §5.3). It avoids redundant Graph calls **within a single multi-step answer** while keeping data near-real-time.

## Acceptance Criteria
- [ ] Cache layer in the SharePoint service with a **configurable TTL**, default 30–60s (D-3, FR-15).
- [ ] A multi-tool answer reuses cached data rather than re-fetching (NFR-4).
- [ ] TTL is a config value, tunable without a code change (D-3).
- [ ] Cache keyed appropriately so different filtered queries are not incorrectly conflated.

## Dependencies
- [[BE-02 SharePoint Service Read Items and Schema]]
