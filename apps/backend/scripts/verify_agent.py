"""
Verification script for BE-05 — LangChain Agent.

Run from apps/backend/:
    uv run python scripts/verify_agent.py

Requires a populated .env (OPENAI_API_KEY, OPENAI_MODEL, Azure + SharePoint creds).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import Settings
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service
from app.agent import build_agent, invoke_agent


async def verify() -> None:
    settings = Settings()
    print("=== BE-05 LangChain Agent Verification ===\n")
    print(f"Model: openai:{settings.openai_model}\n")

    auth = GraphAuthService(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )

    print("1. Connecting to SharePoint...")
    service = await create_sharepoint_service(auth_service=auth, settings=settings)
    print("   OK\n")

    print("2. Building agent...")
    agent = build_agent(service, settings)
    print("   OK\n")

    print("3. Question: What columns are available in this list?")
    answer = await invoke_agent(agent, "What columns are available in this list?")
    print(f"   Answer: {answer[:300]}\n")

    print("4. Question: How many items are in the list?")
    answer = await invoke_agent(agent, "How many items are in the list?")
    print(f"   Answer: {answer}\n")

    print("5. Question: What is the weather today? (should politely decline)")
    answer = await invoke_agent(agent, "What is the weather today?")
    print(f"   Answer: {answer}\n")

    print("=== Verification complete ===")


if __name__ == "__main__":
    asyncio.run(verify())
