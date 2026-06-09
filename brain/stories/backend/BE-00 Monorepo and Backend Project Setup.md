---
id: BE-00
title: Monorepo & Backend Project Setup
tag: done
epic: Foundation
phase: Phase 1 — Foundation
prd_refs: [§6.1]
arch_refs: [§3.2, §7]
python_version: "3.13"
created: 2026-06-04
---

# BE-00 — Monorepo & Backend Project Setup

## Story
As a developer, I want the FastAPI backend scaffolded inside a shared monorepo so that frontend and backend live in one repository with consistent tooling, scripts, and CI.

## Context
The project uses a **monorepo** holding both the Next.js frontend and the Python FastAPI backend (Architecture §3, §7). This story establishes the repo layout and the backend package skeleton.

**Runtime:** Python **3.13**.

## Acceptance Criteria
- [ ] Monorepo root established with a clear `apps/backend/` + `apps/frontend/` split and a top-level README describing layout.
- [ ] Python **3.13** specified in `pyproject.toml` (`requires-python = ">=3.13"`) and `.python-version` file.
- [ ] Python backend package created (FastAPI app entrypoint, dependency manifest — `pyproject.toml`).
- [ ] Core dependencies pinned: `fastapi`, `uvicorn`, `langchain`, `langchain-openai`, `msgraph-sdk`, `azure-identity`, `msal`.
- [ ] Local dev run documented (`uvicorn` dev server) with a health-check endpoint (`GET /health`) returning 200.
- [ ] `.env.example` lists required config keys (Azure OpenAI, Entra, SharePoint site/list, cache TTL). No real secrets committed (NFR-1).
- [ ] Linting (`ruff`) and test runner (`pytest`) configured.
- [ ] `Dockerfile` targets Python 3.13 base image for the container-based deployment target (Azure Container Apps).

## Dependencies
- None (first backend story). Coordinates with [[FE-00 Monorepo and Frontend Project Setup]] on shared monorepo root.
