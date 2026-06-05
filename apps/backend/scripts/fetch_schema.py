"""
Fetch the SharePoint list schema and write src/app/data/sharepoint_schema.md
(loaded into the agent system prompt at startup).

Run from apps/backend/:
    uv run python scripts/fetch_schema.py

Requires a populated .env with all Graph + SharePoint credentials.
Re-run whenever the list columns change.
"""

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import Settings
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service

OUT = Path(__file__).parent.parent / "src" / "app" / "data" / "sharepoint_schema.md"

TYPE_NOTES = {
    "person": "Person/group — fields dict contains {LookupValue, Email}",
    "lookup": "Lookup — fields dict contains {LookupValue}",
    "number": "Numeric — use for sum/average/comparisons",
    "dateTime": "ISO-8601 datetime string",
    "boolean": "true/false",
    "choice": "Choice — one of the configured options",
    "text": "Plain text",
}


async def main() -> None:
    settings = Settings()

    auth = GraphAuthService(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )

    print("Connecting to SharePoint…")
    service = await create_sharepoint_service(auth_service=auth, settings=settings)

    print("Fetching schema…")
    columns = await service.get_schema()
    if not columns:
        print("ERROR: no columns returned")
        sys.exit(1)

    print(f"  {len(columns)} columns found")

    # Fetch a sample item to confirm actual field keys in additional_data
    print("Fetching sample item to verify field keys…")
    items = await service.get_items()
    actual_keys: set[str] = set(items[0].fields.keys()) if items else set()

    lines = [
        "# SharePoint List Schema",
        "",
        f"_Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "Use **Internal Name** when building OData filters or reading `fields` in"
        " tool results.",
        "Always prefix with `fields/` in OData expressions"
        " (e.g. `fields/InternalName eq 'value'`).",
        "",
        "| Display Name | Internal Name | Type | Notes |",
        "|---|---|---|---|",
    ]

    for col in sorted(columns, key=lambda c: c.display_name.lower()):
        present = "✓" if col.name in actual_keys else "⚠ not in sample item"
        suffix = f" — {present}" if present != "✓" else ""
        note = TYPE_NOTES.get(col.column_type, "") + suffix
        lines.append(
            f"| {col.display_name} | `{col.name}` | {col.column_type} | {note} |"
        )

    lines += [
        "",
        "## Person column structure",
        "",
        "When a row is fetched, person/group columns are normalised to:",
        "```json",
        '{ "LookupValue": "Jane Smith", "Email": "jane@example.com" }',
        "```",
        "Filter by name → match `LookupValue`. Filter by email → match `Email`.",
        "",
        "## OData filter examples",
        "",
        "```",
        "fields/Department eq 'CIO'",
        "fields/Status eq 'Active'",
        "```",
        "",
        "Datetime values must be quoted ISO-8601 strings. Match a single day with"
        " a half-open range (not `eq`):",
        "```",
        "fields/Created ge '2026-05-26T00:00:00Z'"
        " and fields/Created lt '2026-05-27T00:00:00Z'",
        "```",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"\nWritten to {OUT}")
    print("\nColumn summary:")
    for col in columns:
        marker = "" if col.name in actual_keys else " ⚠ (not seen in sample)"
        print(
            f"  {col.display_name!r:30s}  internal={col.name!r:30s}"
            f"  type={col.column_type}{marker}"
        )


if __name__ == "__main__":
    asyncio.run(main())
