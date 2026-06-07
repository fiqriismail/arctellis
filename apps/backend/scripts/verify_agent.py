"""
Verification script for BE-05 — LangChain Agent.

Run from apps/backend/:
    uv run python scripts/verify_agent.py

Requires a populated .env (Azure OpenAI, Entra ID + SharePoint creds).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.agent import build_agent, invoke_agent
from app.config import Settings
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service


async def verify() -> None:
    settings = Settings()
    print("=== BE-05 LangChain Agent Verification ===\n")
    print(f"Model: azure_openai:{settings.azure_openai_deployment}\n")

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
    if not answer or len(answer) < 20:
        print("   FAIL — answer looks too short, agent may not have called get_schema")
        sys.exit(1)

    print("4. Question: How many items are in the list?")
    answer = await invoke_agent(agent, "How many items are in the list?")
    print(f"   Answer: {answer}\n")
    if not any(c.isdigit() for c in answer):
        print(
            "   FAIL — answer contains no number, agent may not have called count_rows"
        )
        sys.exit(1)

    print("5. Question: What is the weather today? (should politely decline)")
    answer = await invoke_agent(agent, "What is the weather today?")
    print(f"   Answer: {answer}\n")

    print("=== Verification complete ===")


if __name__ == "__main__":
    asyncio.run(verify())
