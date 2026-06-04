"""
Verification script for BE-02 — SharePoint Service.

Run from apps/backend/:
    uv run python scripts/verify_sharepoint.py

Requires a populated .env with all Graph + SharePoint credentials.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import Settings
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service


async def verify() -> None:
    settings = Settings()
    print("=== BE-02 SharePoint Service Verification ===\n")

    auth = GraphAuthService(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )

    print(f"1. Resolving site and connecting to list {settings.sharepoint_list_id}...")
    service = await create_sharepoint_service(auth_service=auth, settings=settings)
    print("   OK — SharePointService created\n")

    print("2. Reading list schema...")
    columns = await service.get_schema()
    if not columns:
        print("   FAIL — no columns returned")
        sys.exit(1)
    print(f"   OK — {len(columns)} columns found:")
    for col in columns:
        print(f"      {col.name!r:30s} ({col.column_type})")
    print()

    print("3. Reading list items (first page)...")
    items = await service.get_items()
    if items is None:
        print("   FAIL — get_items returned None")
        sys.exit(1)
    print(f"   OK — {len(items)} items returned")
    if items:
        print("   First item fields:")
        for key, val in list(items[0].fields.items())[:5]:
            print(f"      {key}: {val!r}")
    print()

    print("=== Verification complete — SharePoint service is working ===")


if __name__ == "__main__":
    asyncio.run(verify())
