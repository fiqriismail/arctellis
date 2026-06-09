---
id: BE-05
title: LangChain Agent + OpenAI Wiring
tag: done
epic: Agent Core
phase: Phase 2 — Agent core
prd_refs:
  - FR-7
  - FR-10
  - FR-11
  - NFR-6
  - §6.3
arch_refs:
  - §3.3
created: 2026-06-04
---

# BE-05 — LangChain Agent + OpenAI Wiring

## Story
As the backend, I want a LangChain agent connected to OpenAI with tool calling so that the model can interpret a question, choose the right List Data tools, and phrase an answer.

## Context
The agent understands the question and phrases the answer — nothing else (Architecture §3.3). Uses `create_agent()` from `langchain.agents` (backed by LangGraph); model initialised via `init_chat_model("openai:...")` from `langchain.chat_models`. `langchain-openai` remains the provider package. Tools defined with the `@tool` decorator from `langchain.tools`.

## Acceptance Criteria
- [ ] LangChain agent created with `create_agent(model=..., tools=[...], system_prompt=...)` from `langchain.agents`.
- [ ] Model initialised via `init_chat_model(f"openai:{settings.openai_model}")` — `OPENAI_API_KEY` and `OPENAI_MODEL` read from config/settings.
- [ ] List Data tools defined with `@tool` decorator (type hints + docstring as schema) and registered with the agent.
- [ ] The model **decides** which tool(s) to call; it does not compute facts itself (FR-7).
- [ ] Ambiguous questions / non-existent columns → the agent asks a **clarifying question** (FR-10).
- [ ] Questions unrelated to the list → polite decline, no fabrication (FR-11, NFR-6).
- [ ] End-to-end tool calling demonstrated for a representative question (Phase 2 exit).

## Dependencies
- [[BE-04 List Data Tools]]
