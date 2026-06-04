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

    @tool
    async def count_rows(odata_filter: str = "") -> str:
        """Count the number of rows in the SharePoint list matching an
        optional filter (OData expression, e.g. \"fields/Status eq 'Active'\").
        Leave odata_filter empty to count all rows.
        Returns the count as a plain number."""
        items = await service.get_items(odata_filter=odata_filter or None)
        return str(len(items))

    @tool
    async def sum_column(column_name: str, odata_filter: str = "") -> str:
        """Sum the values of a numeric column in the SharePoint list.
        column_name: exact column name as returned by get_schema.
        odata_filter: optional OData filter expression.
        Rows whose value cannot be parsed as a number are silently skipped.
        Returns the total as a number."""
        items = await service.get_items(odata_filter=odata_filter or None)
        total = 0.0
        parsed_count = 0
        for item in items:
            val = _parse_number(item.fields.get(column_name))
            if val is not None:
                total += val
                parsed_count += 1
        if parsed_count == 0:
            return f"No parseable numeric values found in column '{column_name}'."
        return str(total)

    @tool
    async def average_column(column_name: str, odata_filter: str = "") -> str:
        """Calculate the average of a numeric column in the SharePoint list.
        column_name: exact column name as returned by get_schema.
        odata_filter: optional OData filter expression.
        Rows whose value cannot be parsed as a number are silently skipped.
        Returns the average as a number."""
        items = await service.get_items(odata_filter=odata_filter or None)
        total = 0.0
        parsed_count = 0
        for item in items:
            val = _parse_number(item.fields.get(column_name))
            if val is not None:
                total += val
                parsed_count += 1
        if parsed_count == 0:
            return f"No parseable numeric values found in column '{column_name}'."
        return str(total / parsed_count)

    return [get_schema, filter_rows, count_rows, sum_column, average_column]


def _parse_number(value: Any) -> float | None:
    """Return value as float, or None if it cannot be parsed."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
