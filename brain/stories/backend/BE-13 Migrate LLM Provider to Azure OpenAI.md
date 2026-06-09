---
id: BE-13
title: Migrate LLM Provider to Azure OpenAI
tag: done
epic: Deploy
phase: Phase 5 — Deploy
prd_refs:
  - NFR-1
  - D-5
  - §6.3
arch_refs:
  - §3.3
  - §6.4
  - §7
created: 2026-06-07
---

# BE-13 — Migrate LLM Provider to Azure OpenAI

## Story
As the team, I want the agent to call **Azure OpenAI** instead of public OpenAI so that the LLM runs inside our Azure tenant under managed identity, aligning the implementation with the target architecture and our data-governance requirements.

## Context
The architecture and PRD always targeted **Azure OpenAI** (Story Board stack, BE-12 stores "Azure OpenAI keys" in Key Vault, BE-05 was titled "LangChain Agent and Azure OpenAI"). The implementation in [[BE-05 LangChain Agent and OpenAI Wiring]] shipped against **public OpenAI** as an interim shortcut — `agent.py` uses `ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key)` and config exposes `openai_api_key` / `openai_model`. This story corrects that deviation.

Azure OpenAI differs from public OpenAI in three ways the code must account for:
- It is addressed by an **endpoint + deployment name** (not a bare model name) plus an **API version**.
- Authentication should use the container's **managed identity** (Entra ID bearer token) rather than a static key, consistent with how Graph auth already works (`azure-identity`) and with NFR-1 / D-5 (no secrets in code). A key-based fallback is acceptable for local dev only.
- The LangChain provider class is `AzureChatOpenAI` (or `init_chat_model` with provider `azure_openai`); `langchain-openai` already provides it, so no new dependency.

The migration must be transparent to the frontend — the SSE conversation contract ([[BE-06 Conversation Endpoint with SSE Streaming]]) is unchanged. **No frontend story is required** (the frontend never references the LLM provider).

## Acceptance Criteria
- [x] `agent.py` uses `AzureChatOpenAI` (or `init_chat_model("azure_openai:...")`) in place of `ChatOpenAI`.
- [x] Config (`config.py`) exposes Azure settings: `azure_openai_endpoint`, `azure_openai_deployment`, `azure_openai_api_version`; legacy `openai_*` settings removed.
- [x] Authentication via **managed identity / `DefaultAzureCredential`** using a bearer-token provider for scope `https://cognitiveservices.azure.com/.default` (reuses the existing `azure-identity` dependency). Static API key supported only as a local-dev fallback.
- [x] `.env.example` updated with the new Azure variables; secrets remain out of source control (NFR-1).
- [x] Unit tests cover both auth paths (api-key + managed identity) with provider construction mocked — no live calls in CI. Full backend suite green (128 passed).
- [ ] Token **streaming verified** end-to-end against a live Azure OpenAI deployment — `on_chat_model_stream` / `on_chat_model_end` events flow through the SSE endpoint (pending an Azure OpenAI resource).
- [ ] Azure OpenAI secrets/config wired into **Azure Key Vault** alongside [[BE-12 Key Vault Secrets and Container Deployment]] (D-5) — done as part of BE-12 deployment.
- [ ] BE-05 note and the Backend Story Board reflect the corrected provider once merged.

## Implementation notes (2026-06-07)
- **PR [#32](https://github.com/arctellis/group-one-rtp/pull/32) — MERGED to `main`** (`b31d514`, rebased onto latest `main`). Code migration is complete and in `main`; tag stays `review` until token streaming is verified against a live Azure OpenAI deployment. LLM construction extracted to `_build_llm(settings)` in `agent.py`: api-key path when `AZURE_OPENAI_API_KEY` is set, otherwise `get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")`.
- Verified compatibility with Azure AI Foundry `*.cognitiveservices.azure.com` endpoints (Chat Completions surface) — `AZURE_OPENAI_ENDPOINT` is the base host only; the managed-identity scope matches that domain.
- Full backend suite green (155 passed) after rebasing in the BE-08/09/10/11 work.
- **Local dev action required:** populate `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_DEPLOYMENT` (and `AZURE_OPENAI_API_KEY` for local) in `apps/backend/.env`; the old `OPENAI_*` vars are no longer read.
- Remaining unchecked ACs are Azure-resource / deployment dependent and land with BE-12.

## Dependencies
- [[BE-05 LangChain Agent and OpenAI Wiring]]
- [[BE-12 Key Vault Secrets and Container Deployment]]

## Notes
- The deployment name is set in the Azure OpenAI resource and may differ from the underlying model id (e.g. a deployment named `gpt-4o-prod` serving `gpt-4o`). Config must use the **deployment** name.
- Pin a known-good `azure_openai_api_version` (e.g. a recent GA version) rather than tracking latest, to avoid silent behaviour changes.
