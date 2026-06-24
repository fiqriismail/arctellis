import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import build_agent
from app.auth import require_group_member
from app.config import get_settings
from app.routers.chat import router as chat_router
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service

# Attach a stdout handler to the root logger so the app's structured logs
# (BE-10) are emitted; without basicConfig they would be dropped.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


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
        app.state.auth_service = auth
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

    application = FastAPI(
        title="Group One RTP Backend", version="0.1.0", lifespan=lifespan
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(chat_router)
    return application


app = create_app()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/access")
async def access_check(claims: dict = Depends(require_group_member)) -> dict[str, str]:
    return {"access": "granted"}
