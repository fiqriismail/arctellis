from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from app.services.sharepoint import SharePointService


def make_tools(service: SharePointService) -> list:
    """Return LangChain @tool callables wired to the given SharePointService."""

    @tool
    async def get_schema() -> str:
        """Return the column names and data types for the SharePoint list.
        Always call this first to understand the available columns before
        running any query."""
        columns = await service.get_schema()
        if not columns:
            return "No columns found in the list."
        lines = [f"- {col.name} ({col.column_type})" for col in columns]
        return "List columns:\n" + "\n".join(lines)

    @tool
    async def filter_rows(odata_filter: str = "") -> str:
        """Retrieve rows from the SharePoint list, optionally filtered by an
        OData expression (e.g. \"fields/Status eq 'Active'\").
        Leave odata_filter empty to retrieve all rows.
        Returns the row data as JSON."""
        items = await service.get_items(odata_filter=odata_filter or None)
        if not items:
            return "No rows found."
        rows = [item.fields for item in items]
        return json.dumps(rows, default=str)

    return [get_schema, filter_rows]


def _parse_number(value: Any) -> float | None:
    """Return value as float, or None if it cannot be parsed."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
