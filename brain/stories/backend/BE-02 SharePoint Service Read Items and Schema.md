---
id: BE-02
title: SharePoint Service — Read Items & Schema
tag: done
epic: Foundation
phase: Phase 1 — Foundation
prd_refs:
  - FR-12
  - FR-13
  - FR-14
  - §8
arch_refs:
  - §3.5
  - §5.1
created: 2026-06-04
---

# BE-02 — SharePoint Service: Read Items & Schema

## Story
As the backend, I want a SharePoint service module that reads list items and the list schema through Microsoft Graph so that downstream tools have data and column metadata to work with.

## Context
The SharePoint service wraps all Graph calls (Architecture §3.5). Site URL and list ID are **configuration**, not hard-coded (FR-13, D-4); structure is discovered at runtime (FR-14).

## Acceptance Criteria
- [ ] Service reads list items via Graph (`msgraph-sdk`) for a configured site + list ID (FR-12, FR-13).
- [ ] Service returns the list's **column names and types** (FR-14) so the model can reference real fields.
- [ ] Internal vs display field names handled — schema exposes names the model can reliably use (§8).
- [ ] Loosely-typed values parsed defensively (numbers/dates/choice); unparseable values handled without crashing (§5.1, §8).
- [ ] Verified with a Phase 1 script/test harness reading the real (or a sample) list.

## Dependencies
- [[BE-01 Entra App Registration and Graph Auth]]
