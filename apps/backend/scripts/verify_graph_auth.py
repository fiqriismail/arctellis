"""
Verification script for BE-01 — Graph auth.

Run from apps/backend/:
    uv run python scripts/verify_graph_auth.py

Requires a populated .env with:
    AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
Optionally:
    SHAREPOINT_SITE_URL  (enables a live Graph site lookup)
"""

import asyncio
import sys
from urllib.parse import urlparse

from app.config import Settings
from app.services.graph_auth import GraphAuthService


async def verify() -> None:
    settings = Settings()  # reads .env in cwd

    print("=== BE-01 Graph Auth Verification ===\n")

    # Step 1: acquire a token
    print("1. Acquiring Graph token via client-credentials...")
    service = GraphAuthService(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )
    credential = service.get_credential()
    token = credential.get_token("https://graph.microsoft.com/.default")

    if not token.token:
        print("   FAIL — token is empty")
        sys.exit(1)

    print(f"   OK — token acquired (expires: {token.expires_on})\n")

    # Step 2: make a real Graph call if site URL is configured
    if settings.sharepoint_site_url:
        print(f"2. Verifying Graph access to: {settings.sharepoint_site_url}")
        parsed = urlparse(settings.sharepoint_site_url)
        hostname = parsed.netloc
        site_path = parsed.path.rstrip("/")

        client = service.get_client()
        try:
            site = await client.sites.by_site_id(f"{hostname}:{site_path}").get()
            print(f"   OK — site accessible: {site.display_name}\n")
        except Exception as exc:
            print(f"   FAIL — Graph call raised: {exc}")
            sys.exit(1)
    else:
        print("2. SHAREPOINT_SITE_URL not set — skipping live Graph site lookup")
        print("   (Set it in .env to test the full permissions grant)\n")

    print("=== Verification complete — Graph auth is working ===")


if __name__ == "__main__":
    asyncio.run(verify())
