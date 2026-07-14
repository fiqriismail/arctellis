# Arctellis RTP — SharePoint List AI Assistant

A conversational AI assistant for querying SharePoint list data in plain English.

## Monorepo layout

```
apps/
  backend/   Python 3.13 · FastAPI · LangChain · Microsoft Graph
  frontend/  Next.js 16.x · shadcn/ui (light theme)
docs/        PRD, Architecture, stories
```

## Quick start

> **Prerequisites:** Run these commands after scaffolding is complete (the apps are set up in subsequent tasks).

### Backend
```bash
cd apps/backend
uv sync
cp .env.example .env   # fill in your values
uv run uvicorn app.main:app --app-dir src --reload
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
