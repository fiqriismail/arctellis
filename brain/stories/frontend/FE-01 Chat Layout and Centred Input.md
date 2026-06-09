---
id: FE-01
title: Chat Layout & Centred Input
tag: done
epic: Chat UI
phase: Phase 3 — Chat UI
prd_refs:
  - FR-1
arch_refs:
  - §3.1
created: 2026-06-04
---

# FE-01 — Chat Layout & Centred Input

## Story
As a user, I want a clean, minimal chat screen with a single centred text input so that I can ask a question without dealing with filters, dropdowns, or forms.

## Context
A single centred text input is the primary control — no filter panels or form fields (PRD FR-1). Built with Next.js + shadcn/ui, light theme (Architecture §3.1).

## Acceptance Criteria
- [ ] A single, centred text input is the primary control (FR-1).
- [ ] No filter panels, dropdowns, or form fields present (FR-1).
- [ ] Built with shadcn/ui components, light theme.
- [ ] Submit via button and Enter key; empty submissions prevented.
- [ ] Responsive, clean layout modelled on a modern AI assistant client.

## Dependencies
- [[FE-00 Monorepo and Frontend Project Setup]]
