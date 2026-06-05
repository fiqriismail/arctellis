from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import build_agent
from app.config import get_settings
from app.routers.chat import router as chat_router
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Skipped in tests: test fixtures set app.state.agent before requests.
    if not hasattr(app.state, "agent"):
        settings = get_settings()
        auth = GraphAuthService(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )
        service = await create_sharepoint_service(auth_service=auth, settings=settings)
        app.state.agent = build_agent(service, settings)
    yield


app = FastAPI(title="Group One RTP Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
