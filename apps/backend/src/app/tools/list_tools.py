from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from app.services.sharepoint import SharePointService


def _local_day_range_utc(
    start_date: str, end_date: str, site_timezone: str
) -> tuple[str, str]:
    """Convert a local calendar day (or inclusive range) to a UTC half-open range.

    start_date / end_date are 'YYYY-MM-DD' in site_timezone. Returns
    (start_utc, end_utc) as quoted-ready ISO-8601 'Z' strings, where end_utc is
    exclusive (00:00 local of the day after end_date). Raises ValueError on bad
    input.
    """
    zone = ZoneInfo(site_timezone)
    start_local = datetime.fromisoformat(start_date).replace(tzinfo=zone)
    last_day = datetime.fromisoformat(end_date) if end_date else start_local
    end_local = (last_day + timedelta(days=1)).replace(tzinfo=zone)

    def _to_utc(d: datetime) -> str:
        return d.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    return _to_utc(start_local), _to_utc(end_local)


def make_tools(service: SharePointService, site_timezone: str = "UTC") -> list:
    """Return LangChain @tool callables wired to the given SharePointService.

    site_timezone is the IANA zone in which user-typed calendar dates are
    interpreted before converting to the UTC range Graph filters on.
    """

    @tool
    async def get_schema() -> str:
        """Return the column names and data types for the SharePoint list.
        Always call this first to understand the available columns before
        running any query."""
        columns = await service.get_schema()
        if not columns:
            return "No columns found in the list."
        lines = [
            f"- internal_name={col.name!r}  display_name={col.display_name!r}"
            f"  type={col.column_type}"
            for col in columns
        ]
        return (
            "List columns (use internal_name when querying fields or building"
            " filters):\n" + "\n".join(lines)
        )

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
    async def filter_by_date(
        column_name: str, start_date: str, end_date: str = ""
    ) -> str:
        """Retrieve rows where a date/time column falls on a local calendar day
        or range. ALWAYS use this for any question about a date or day on a
        date/time column (e.g. Created, Modified) instead of building a datetime
        OData filter yourself — it handles timezone conversion correctly.
        column_name: internal name of a dateTime column (e.g. 'Created').
        start_date: 'YYYY-MM-DD' interpreted in the site's local timezone.
        end_date: optional inclusive end 'YYYY-MM-DD'; omit for a single day.
        Returns the matching rows as JSON."""
        try:
            start_utc, end_utc = _local_day_range_utc(
                start_date, end_date, site_timezone
            )
        except ValueError:
            return "Invalid date. Use the format YYYY-MM-DD."
        odata = (
            f"fields/{column_name} ge '{start_utc}' "
            f"and fields/{column_name} lt '{end_utc}'"
        )
        items = await service.get_items(odata_filter=odata)
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
        odata_filter: optional OData filter expression. IMPORTANT: always
          prefix column names with 'fields/' (e.g. "fields/Status eq 'Active'").
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
        odata_filter: optional OData filter expression. IMPORTANT: always
          prefix column names with 'fields/' (e.g. "fields/Status eq 'Active'").
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

    @tool
    async def group_and_aggregate(
        group_by_column: str,
        aggregate_column: str,
        aggregate_func: str,
        odata_filter: str = "",
    ) -> str:
        """Group rows by one column and aggregate another column.
        group_by_column: column to group by (exact name from get_schema).
        aggregate_column: column to aggregate (exact name from get_schema).
        aggregate_func: one of 'count', 'sum', or 'average'.
          - count: count all rows in each group.
          - sum: sum numeric values in aggregate_column per group.
          - average: average numeric values in aggregate_column per group.
        odata_filter: optional OData filter applied before grouping. IMPORTANT:
          always prefix column names with 'fields/' (e.g. "fields/Status eq 'Active'").
        Rows whose aggregate_column cannot be parsed as a number are skipped
        (for sum and average only).
        Returns one line per group: 'group_value: result'."""
        if aggregate_func not in ("count", "sum", "average"):
            return (
                f"Invalid aggregate_func '{aggregate_func}'. "
                "Must be 'count', 'sum', or 'average'."
            )
        items = await service.get_items(odata_filter=odata_filter or None)
        if not items:
            return "No rows found."

        groups: dict[str, list[Any]] = {}
        for item in items:
            group_val = str(item.fields.get(group_by_column) or "(blank)")
            if group_val not in groups:
                groups[group_val] = []
            groups[group_val].append(item.fields.get(aggregate_column))

        lines = []
        for group_val, vals in sorted(groups.items()):
            if aggregate_func == "count":
                agg_result = str(len(vals))
            elif aggregate_func == "sum":
                nums = [_parse_number(v) for v in vals]
                nums = [n for n in nums if n is not None]
                no_values_msg = "No parseable numeric values in this group."
                agg_result = str(sum(nums)) if nums else no_values_msg
            else:  # average
                nums = [_parse_number(v) for v in vals]
                nums = [n for n in nums if n is not None]
                no_values_msg = "No parseable numeric values in this group."
                agg_result = str(sum(nums) / len(nums)) if nums else no_values_msg
            lines.append(f"{group_val}: {agg_result}")
        return "\n".join(lines)

    return [
        get_schema,
        filter_rows,
        filter_by_date,
        count_rows,
        sum_column,
        average_column,
        group_and_aggregate,
    ]


def _parse_number(value: Any) -> float | None:
    """Return value as float, or None if it cannot be parsed."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
