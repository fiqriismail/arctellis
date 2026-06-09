---
id: BE-12
title: Key Vault Secrets & Container Deployment
tag: todo
epic: Deploy
phase: Phase 5 — Deploy
prd_refs: [NFR-1, D-5, §6.1]
arch_refs: [§6.4, §7]
created: 2026-06-04
---

# BE-12 — Key Vault Secrets & Container Deployment

## Story
As the team, I want the backend deployed as a container with secrets in Azure Key Vault so that the service runs in Azure with no secrets in code or source control.

## Context
Backend deploys as a container-based app (Azure Container Apps); secrets live in Key Vault and are read at runtime via the container's managed identity (Architecture §7, NFR-1, D-5).

## Acceptance Criteria
- [ ] All secrets (Azure OpenAI keys, Entra client secret, connection settings) stored in **Azure Key Vault** (NFR-1).
- [ ] Container's **managed identity** granted read access to the vault; secrets resolved at runtime (D-5).
- [ ] No secret in client code or source control (NFR-1).
- [ ] Backend container deployed to Azure Container Apps.
- [ ] Smoke test passes against the deployed backend (Phase 5).

## Dependencies
- [[BE-06 Conversation Endpoint with SSE Streaming]]
- [[BE-10 Observability Logging]]
