# Monorepo Setup (BE-00 + FE-00) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a monorepo containing a Python 3.13 FastAPI backend and a Next.js 16.x frontend, each runnable locally with a health-check / placeholder page, and ready for the next stories to build on.

**Architecture:** Plain `apps/` monorepo — no Turborepo/Nx since there is no shared JS code between the two apps. Backend uses `uv` + `pyproject.toml`; frontend uses `npm` + Next.js App Router. Each app is self-contained under `apps/backend/` and `apps/frontend/`.

**Tech Stack:** Python 3.13 · uv · FastAPI · uvicorn · ruff · pytest · Docker | Next.js 16.x · shadcn/ui (light/zinc) · ESLint · Prettier · TypeScript

**Stories:** BE-00 · FE-00
**Working directory:** repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

---

## File Map

```
group-one-rtp/
├── apps/
│   ├── backend/
│   │   ├── src/
│   │   │   └── app/
│   │   │       ├── __init__.py
│   │   │       └── main.py          ← FastAPI app + /health endpoint
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── test_health.py       ← pytest smoke test
│   │   ├── .python-version          ← pins 3.13
│   │   ├── pyproject.toml           ← deps, ruff, pytest config
│   │   ├── .env.example             ← required config keys
│   │   └── Dockerfile
│   └── frontend/
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx        ← root layout
│       │   │   └── page.tsx          ← placeholder page
│       │   └── features/
│       │       └── chat/             ← vertical slice (empty scaffold)
│       │           └── .gitkeep
│       ├── components.json           ← shadcn/ui config
│       ├── next.config.ts
│       ├── tsconfig.json
│       ├── eslint.config.mjs
│       ├── .prettierrc
│       └── package.json
├── docs/                             ← existing
└── README.md                         ← update with monorepo layout
```

---

## Task 1: Monorepo root structure

**Files:**
- Modify: `README.md`
- Create: `apps/` directory

- [ ] **Step 1.1: Create the apps directory structure**

```bash
mkdir -p apps/backend apps/frontend
```

- [ ] **Step 1.2: Update README.md with monorepo layout**

Replace the contents of `README.md` with:

```markdown
# Group One RTP — SharePoint List AI Assistant

A conversational AI assistant for querying SharePoint list data in plain English.

## Monorepo layout

```
apps/
  backend/   Python 3.13 · FastAPI · LangChain · Microsoft Graph
  frontend/  Next.js 16.x · shadcn/ui (light theme)
docs/        PRD, Architecture, stories
```

## Quick start

### Backend
```bash
cd apps/backend
uv sync
cp .env.example .env   # fill in your values
uv run uvicorn app.main:app --reload
# → http://localhost:8000/health
```

### Frontend
```bash
cd apps/frontend
npm install
cp .env.local.example .env.local   # fill in your values
npm run dev
# → http://localhost:3000
```

## Documentation
- [PRD](docs/PRD-SharePoint-List-AI-Assistant.md)
- [Architecture](docs/Architecture-SharePoint-List-AI-Assistant.md)
```

- [ ] **Step 1.3: Commit**

```bash
git add apps/.gitkeep README.md   # or just the dirs
git add -f apps/backend/.gitkeep apps/frontend/.gitkeep 2>/dev/null; true
git add README.md
git commit -m "chore: initialise monorepo structure (apps/backend, apps/frontend)"
```

---

## Task 2: Backend — pyproject.toml and dependencies

**Files:**
- Create: `apps/backend/pyproject.toml`
- Create: `apps/backend/.python-version`

- [ ] **Step 2.1: Create `.python-version`**

```
3.13
```
File path: `apps/backend/.python-version`

- [ ] **Step 2.2: Create `apps/backend/pyproject.toml`**

```toml
[project]
name = "group-one-rtp-backend"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "langchain>=0.3",
    "langchain-openai>=0.3",
    "msgraph-sdk>=1.10",
    "azure-identity>=1.19",
    "msal>=1.31",
    "python-dotenv>=1.0",
    "pydantic-settings>=2.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.25",
    "httpx>=0.28",
    "ruff>=0.9",
]

[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2.3: Install dependencies**

```bash
cd apps/backend
uv sync --all-extras
```

Expected: uv creates `.venv` and resolves all packages. No errors.

- [ ] **Step 2.4: Commit**

```bash
cd apps/backend
git add pyproject.toml .python-version uv.lock
git commit -m "chore(backend): add pyproject.toml and lock file for Python 3.13"
```

---

## Task 3: Backend — FastAPI app with /health endpoint (TDD)

**Files:**
- Create: `apps/backend/src/app/__init__.py`
- Create: `apps/backend/src/app/main.py`
- Create: `apps/backend/tests/__init__.py`
- Create: `apps/backend/tests/test_health.py`

- [ ] **Step 3.1: Create package init files**

`apps/backend/src/app/__init__.py` — empty file.
`apps/backend/tests/__init__.py` — empty file.

- [ ] **Step 3.2: Write the failing test first**

`apps/backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient


def test_health_returns_200():
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_status_ok():
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3.3: Run tests — verify they FAIL**

```bash
cd apps/backend
uv run pytest tests/test_health.py -v
```

Expected output: `ModuleNotFoundError: No module named 'app'` or `ImportError`. Tests must be red before proceeding.

- [ ] **Step 3.4: Implement the FastAPI app**

`apps/backend/src/app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Group One RTP Backend", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 3.5: Configure pytest to find the `src` layout**

Add to `apps/backend/pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
pythonpath = ["src"]
```

- [ ] **Step 3.6: Run tests — verify they PASS**

```bash
cd apps/backend
uv run pytest tests/test_health.py -v
```

Expected output:
```
PASSED tests/test_health.py::test_health_returns_200
PASSED tests/test_health.py::test_health_returns_status_ok
2 passed
```

- [ ] **Step 3.7: Verify the dev server starts**

```bash
cd apps/backend
uv run uvicorn app.main:app --reload
```

Open `http://localhost:8000/health` — should return `{"status":"ok"}`.
Open `http://localhost:8000/docs` — FastAPI auto-docs should render.
Stop with Ctrl+C.

- [ ] **Step 3.8: Commit**

```bash
cd apps/backend
git add src/ tests/ pyproject.toml
git commit -m "feat(backend): FastAPI app with /health endpoint (BE-00)"
```

---

## Task 4: Backend — .env.example and Dockerfile

**Files:**
- Create: `apps/backend/.env.example`
- Create: `apps/backend/Dockerfile`

- [ ] **Step 4.1: Create `.env.example`**

`apps/backend/.env.example`:

```dotenv
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Entra ID (app registration)
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# SharePoint / Microsoft Graph
SHAREPOINT_SITE_URL=https://<tenant>.sharepoint.com/sites/<site>
SHAREPOINT_LIST_ID=

# Cache
CACHE_TTL_SECONDS=60

# Row threshold before switching to filtered-only retrieval
LIST_ROW_THRESHOLD=1000
```

- [ ] **Step 4.2: Ensure `.env` is gitignored**

Check that `apps/backend/.env` (without `.example`) will never be committed:

```bash
echo "apps/backend/.env" >> .gitignore
echo "apps/frontend/.env.local" >> .gitignore
```

Verify:
```bash
cat .gitignore
```

- [ ] **Step 4.3: Create `apps/backend/Dockerfile`**

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production deps only (no dev extras)
RUN uv sync --frozen --no-dev

# Copy application source
COPY src/ ./src/

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4.4: Commit**

```bash
git add apps/backend/.env.example apps/backend/Dockerfile .gitignore
git commit -m "chore(backend): add .env.example and Dockerfile for Python 3.13 (BE-00)"
```

---

## Task 5: Backend — ruff lint check

**Files:** none new — verifying existing code passes linting.

- [ ] **Step 5.1: Run ruff over the backend source**

```bash
cd apps/backend
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Expected: no errors. If any formatting issues:
```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
```

- [ ] **Step 5.2: Commit any ruff fixes**

```bash
git add apps/backend/src/ apps/backend/tests/
git commit -m "style(backend): apply ruff formatting (BE-00)" --allow-empty
```

---

## Task 6: Frontend — Next.js 16.x scaffold

**Files:**
- Create: all files under `apps/frontend/` generated by `create-next-app`

- [ ] **Step 6.1: Scaffold Next.js 16.x with TypeScript and App Router**

From the repo root:

```bash
cd apps
npx create-next-app@16 frontend \
  --typescript \
  --eslint \
  --app \
  --src-dir \
  --no-tailwind \
  --import-alias "@/*"
```

When prompted about Turbopack — accept the default (yes).

Expected: `apps/frontend/` created with App Router structure under `src/app/`.

- [ ] **Step 6.2: Verify Next.js version**

```bash
cd apps/frontend
cat package.json | grep '"next"'
```

Expected: `"next": "^16.x.x"` (or similar 16.x range).

- [ ] **Step 6.3: Add Prettier**

```bash
cd apps/frontend
npm install --save-dev prettier eslint-config-prettier
```

Create `apps/frontend/.prettierrc`:

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

- [ ] **Step 6.4: Add `.env.local.example`**

`apps/frontend/.env.local.example`:

```dotenv
# Backend API base URL (no trailing slash)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Entra ID (for user sign-in — FE-07)
NEXT_PUBLIC_ENTRA_TENANT_ID=
NEXT_PUBLIC_ENTRA_CLIENT_ID=
```

- [ ] **Step 6.5: Create the vertical slice scaffold**

```bash
mkdir -p apps/frontend/src/features/chat
touch apps/frontend/src/features/chat/.gitkeep
```

- [ ] **Step 6.6: Verify dev server starts**

```bash
cd apps/frontend
npm run dev
```

Open `http://localhost:3000` — the default Next.js page should render. Stop with Ctrl+C.

- [ ] **Step 6.7: Commit**

```bash
git add apps/frontend/
git commit -m "feat(frontend): scaffold Next.js 16.x with App Router and TypeScript (FE-00)"
```

---

## Task 7: Frontend — install and configure shadcn/ui (light theme)

**Files:**
- Modify: `apps/frontend/package.json`
- Create: `apps/frontend/components.json`
- Modify: `apps/frontend/src/app/globals.css`
- Modify: `apps/frontend/src/app/layout.tsx`

- [ ] **Step 7.1: Add Tailwind CSS (required by shadcn/ui)**

shadcn/ui requires Tailwind. Install it:

```bash
cd apps/frontend
npm install tailwindcss @tailwindcss/postcss postcss
```

Create `apps/frontend/postcss.config.mjs`:

```js
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
}
export default config
```

- [ ] **Step 7.2: Initialise shadcn/ui**

```bash
cd apps/frontend
npx shadcn@latest init
```

When prompted:
- **Style:** Default (or New York — pick New York for a cleaner look)
- **Base color:** Zinc
- **CSS variables:** Yes

This creates `components.json` and updates `globals.css` and `layout.tsx`.

- [ ] **Step 7.3: Verify components.json has light theme**

```bash
cat apps/frontend/components.json
```

The file should contain `"style": "new-york"` (or `"default"`) and `"baseColor": "zinc"`. The theme defaults to light — shadcn's CSS variables set a light mode by default.

- [ ] **Step 7.4: Verify the app still renders**

```bash
cd apps/frontend
npm run dev
```

Open `http://localhost:3000` — page still renders (may look different now with Tailwind reset). Stop with Ctrl+C.

- [ ] **Step 7.5: Commit**

```bash
git add apps/frontend/
git commit -m "feat(frontend): install shadcn/ui with light/zinc theme (FE-00)"
```

---

## Task 8: Frontend — update root layout and placeholder page

**Files:**
- Modify: `apps/frontend/src/app/layout.tsx`
- Modify: `apps/frontend/src/app/page.tsx`

- [ ] **Step 8.1: Update root layout**

`apps/frontend/src/app/layout.tsx`:

```tsx
import type { Metadata } from 'next'
import { Geist } from 'next/font/google'
import './globals.css'

const geist = Geist({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Group One RTP — AI Assistant',
  description: 'Ask questions about your SharePoint list in plain English.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={geist.className}>{children}</body>
    </html>
  )
}
```

- [ ] **Step 8.2: Create placeholder page**

`apps/frontend/src/app/page.tsx`:

```tsx
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          SharePoint List AI Assistant
        </h1>
        <p className="text-muted-foreground text-sm">
          Chat UI coming soon — see FE-01.
        </p>
      </div>
    </main>
  )
}
```

- [ ] **Step 8.3: Run lint check**

```bash
cd apps/frontend
npm run lint
```

Expected: no errors.

- [ ] **Step 8.4: Verify final render**

```bash
npm run dev
```

Open `http://localhost:3000` — should show the centred heading "SharePoint List AI Assistant" and subtitle. Stop with Ctrl+C.

- [ ] **Step 8.5: Commit**

```bash
git add apps/frontend/src/app/
git commit -m "feat(frontend): root layout and placeholder page (FE-00)"
```

---

## Task 9: Mark stories done in Obsidian

- [ ] **Step 9.1: Update BE-00 tag to done**

In the vault file `Stories/Backend/BE-00 Monorepo and Backend Project Setup.md`, change frontmatter:

```yaml
tag: done
```

- [ ] **Step 9.2: Update FE-00 tag to done**

In the vault file `Stories/Frontend/FE-00 Monorepo and Frontend Project Setup.md`, change frontmatter:

```yaml
tag: done
```

- [ ] **Step 9.3: Update both Story Boards**

In `Stories/Backend/Story Board.md` and `Stories/Frontend/Story Board.md`, change BE-00 / FE-00 status column from `` `todo` `` to `` `done` ``.

---

## Self-Review

**Spec coverage check:**

| Acceptance criterion | Task |
|---|---|
| Monorepo root with `apps/` split | Task 1 |
| Python 3.13 in `pyproject.toml` + `.python-version` | Task 2 |
| Core backend deps pinned | Task 2 |
| Health-check endpoint returning 200 | Task 3 |
| `.env.example` with all config keys | Task 4 |
| No real secrets committed | Task 4 |
| ruff linting + pytest configured | Tasks 2, 5 |
| Dockerfile targeting Python 3.13 | Task 4 |
| Next.js 16.x App Router in monorepo | Task 6 |
| shadcn/ui light theme initialised | Task 7 |
| Vertical slice `features/chat/` scaffold | Task 6 |
| Backend base URL from env var | Task 6 |
| ESLint + Prettier configured | Tasks 6, 8 |
| Dev server renders placeholder page | Task 8 |

All criteria covered. No placeholders. Types consistent throughout.
