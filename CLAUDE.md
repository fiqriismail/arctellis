# CLAUDE.md — Arctellis RTP

## Project

SharePoint List AI Assistant — a web app that answers plain-English questions about a SharePoint list. This is a **monorepo** containing a Python backend and a Next.js frontend under `apps/`.

## Tech stack and versions

| Layer | Technology | Version |
|---|---|---|
| Backend language | Python | 3.13 |
| Backend framework | FastAPI + uvicorn | >=0.115 / >=0.34 |
| Package manager (backend) | uv | 0.6.x |
| AI orchestration | LangChain + langchain-core + langchain-openai + langgraph | >=1.0 |
| LLM | OpenAI via `init_chat_model("openai:...")` | via langchain-openai |
| Graph access | msgraph-sdk + azure-identity | >=1.10 / >=1.19 |
| Linting / formatting | ruff | >=0.9 |
| Test runner | pytest + pytest-asyncio | >=8.3 / >=0.25 |
| Frontend language | TypeScript | strict mode |
| Frontend framework | Next.js (App Router) | ^16.2.7 |
| Package manager (frontend) | npm | 11.x |
| UI components | shadcn/ui | v4.x (base-luma / zinc, light theme) |
| CSS | Tailwind CSS | v4.x |

Always use these exact versions. Do not introduce alternative libraries without discussion.

## Coding conventions

- **Architecture:** vertical slicing — features own their components, hooks, API client, and types together.
- **UI:** shadcn/ui components only, light theme. No hard-coded colours — use CSS variable utility classes (`bg-background`, `text-foreground`, `text-muted-foreground`, etc.).
- **Backend:** `src/` layout (`apps/backend/src/app/`). Run uvicorn with `--app-dir src`.
- **Secrets:** never committed. Use `.env` locally (gitignored). In production, secrets come from Azure Key Vault via managed identity.
- **TDD:** write the failing test first, confirm red, implement, confirm green, then commit.
- **Commits:** conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `style:`). Include the story ID in the message where applicable, e.g. `feat(backend): add count_rows tool (BE-04)`.

## Memory — Local brain directory

Project memory, stories, and decisions live in the local `brain/` directory. Read and write these notes directly as local markdown files.

- **Stories** are in `brain/Stories/Backend/` and `brain/Stories/Frontend/`. Each story note has a `tag` frontmatter field holding its status: `todo` · `in-progress` · `review` · `done`.
- **Story Boards** (`brain/Story Board - Backend.md`, `brain/Story Board - Frontend.md`) index all stories with their current status. Keep these in sync whenever a story tag changes.
- **PRD and Architecture** docs are in `docs/` in this repo (the canonical source). The brain directory may link to them but the repo files are authoritative.

## After each story is completed

1. Mark the story `tag` to `done` in its note within `brain/` and update the Story Board.
2. Add a **daily note** in the local `brain/` directory (e.g., `brain/Daily Notes/<YYYY-MM-DD>.md`) recording what was completed. Append this content:
   ```markdown
   - Completed [STORY-ID] [Story title]
   ```
   Include the story ID, a one-line summary of what was built, and any notable decisions or deviations from the plan.

## Key documents

- PRD: `docs/PRD-SharePoint-List-AI-Assistant.md`
- Architecture: `docs/Architecture-SharePoint-List-AI-Assistant.md`
- Implementation plans: `docs/superpowers/plans/`
