from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.sites.item.lists.item.items import items_request_builder

logger = logging.getLogger(__name__)


class _TTLCache:
    """Simple in-memory TTL cache backed by a dict and monotonic timestamps."""

    def __init__(self, ttl: int) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.monotonic() >= expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (value, time.monotonic() + self._ttl)


@dataclass
class ColumnDefinition:
    name: str
    display_name: str
    # column_type: "text" | "number" | "dateTime" | "choice" | "boolean"
    # | "lookup" | "person" | "other"
    column_type: str


@dataclass
class ListItem:
    id: str
    fields: dict[str, Any]


class SharePointService:
    def __init__(
        self,
        client: GraphServiceClient,
        site_id: str,
        list_id: str,
        cache_ttl: int = 60,
    ) -> None:
        self._client = client
        self._site_id = site_id
        self._list_id = list_id
        self._cache = _TTLCache(ttl=cache_ttl)
        # Resolved User Information List entries: {lookup_id: {LookupValue, Email}}.
        # Users change rarely, so resolutions are cached for the process lifetime.
        self._user_cache: dict[str, dict] = {}

    @staticmethod
    def _infer_column_type(col: Any) -> str:
        if col.number is not None:
            return "number"
        if col.date_time is not None:
            return "dateTime"
        if col.boolean is not None:
            return "boolean"
        if col.choice is not None:
            return "choice"
        if col.lookup is not None:
            return "lookup"
        if col.person_or_group is not None:
            return "person"
        return "text"

    @staticmethod
    def _safe_parse(value: Any, column_type: str) -> Any:
        if value is None:
            return None
        if column_type == "number":
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        if column_type == "dateTime":
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return None
            return None
        if column_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        return str(value)

    async def get_schema(self) -> list[ColumnDefinition]:
        cached = self._cache.get("schema")
        if cached is not None:
            return cached
        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .columns.get()
        )
        columns: list[ColumnDefinition] = []
        if not result or not result.value:
            self._cache.set("schema", columns)
            return columns
        for col in result.value:
            if col.hidden or not col.name:
                continue
            columns.append(
                ColumnDefinition(
                    name=col.name,
                    display_name=col.display_name or col.name,
                    column_type=self._infer_column_type(col),
                )
            )
        self._cache.set("schema", columns)
        return columns

    async def _person_field_names(self) -> set[str]:
        """Internal names of columns whose type is 'person', from the schema."""
        columns = await self.get_schema()
        return {c.name for c in columns if c.column_type == "person"}

    async def _resolve_user_ids(self, ids: set[str]) -> dict[str, dict]:
        """Resolve User Information List item ids to {LookupValue, Email}.

        Graph returns person columns only as '{Field}LookupId' holding a numeric
        id into the site's hidden 'User Information List'. We fetch each id from
        that list (Title = display name, EMail = email) and cache the result.
        """
        resolved: dict[str, dict] = {}
        for uid in ids:
            if uid in self._user_cache:
                resolved[uid] = self._user_cache[uid]
                continue
            try:
                item = await (
                    self._client.sites.by_site_id(self._site_id)
                    .lists.by_list_id("User Information List")
                    .items.by_list_item_id(uid)
                    .get()
                )
                ad = item.fields.additional_data if item and item.fields else {}
                info = {"LookupValue": ad.get("Title"), "Email": ad.get("EMail")}
            except Exception:
                logger.warning("Could not resolve User Information List id %s", uid)
                info = {"LookupValue": None, "Email": None}
            self._user_cache[uid] = info
            resolved[uid] = info
        return resolved

    @staticmethod
    def _merge_person_fields(
        fields: dict[str, Any],
        person_names: set[str],
        user_map: dict[str, dict],
    ) -> dict[str, Any]:
        """Replace '{Person}LookupId' keys with resolved {LookupValue, Email}.

        Pure function: given raw fields, the set of person-column internal names,
        and an id->info map, return fields with each person column populated under
        its internal name and the raw LookupId key removed. Non-person lookups
        (e.g. Category) are left untouched.
        """
        unresolved = {"LookupValue": None, "Email": None}
        out = dict(fields)
        for name in person_names:
            key = f"{name}LookupId"
            if key not in out:
                continue
            raw = out.pop(key)
            if isinstance(raw, list):
                out[name] = [user_map.get(str(i), unresolved) for i in raw]
            else:
                out[name] = user_map.get(str(raw), unresolved)
        return out

    @staticmethod
    def _normalize_filter(f: str) -> str:
        """Prepend 'fields/' to bare column names in OData filter expressions.

        SharePoint Graph requires 'fields/ColumnName eq value' — bare column
        names (without a path separator) are invalid. The LLM sometimes omits
        the prefix, so we patch it up here as a safety net.
        """
        def _prefix(match: re.Match) -> str:
            prop, op = match.group(1), match.group(2)
            return f"fields/{prop} {op}"

        return re.sub(
            r"(?<!/)\b([A-Za-z_]\w*)\s+(eq|ne|lt|le|gt|ge|startswith|endswith|contains)\b",
            _prefix,
            f,
            flags=re.IGNORECASE,
        )

    async def get_items(self, odata_filter: str | None = None) -> list[ListItem]:
        if odata_filter:
            odata_filter = self._normalize_filter(odata_filter)
        cache_key = f"items:{odata_filter or ''}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        builder = items_request_builder.ItemsRequestBuilder
        query_params = builder.ItemsRequestBuilderGetQueryParameters(expand=["fields"])
        if odata_filter:
            query_params.filter = odata_filter

        request_configuration = RequestConfiguration(query_parameters=query_params)

        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .items.get(request_configuration=request_configuration)
        )

        # Note: only fetches first page (~200 items). Pagination via
        # odata_next_link not implemented.
        items: list[ListItem] = []
        if not result or not result.value:
            self._cache.set(cache_key, items)
            return items

        raw_items: list[tuple[str, dict[str, Any]]] = []
        for item in result.value:
            raw: dict[str, Any] = {}
            if item.fields and item.fields.additional_data:
                raw = dict(item.fields.additional_data)
            raw_items.append((item.id or "", raw))

        # Person columns arrive only as '{Field}LookupId' numeric ids. Resolve
        # them to display names + emails. Skip entirely when no lookup keys are
        # present (keeps the common path free of extra Graph calls).
        has_lookup = any(
            k.endswith("LookupId") for _, raw in raw_items for k in raw
        )
        if has_lookup:
            person_names = await self._person_field_names()
            needed: set[str] = set()
            for _, raw in raw_items:
                for name in person_names:
                    val = raw.get(f"{name}LookupId")
                    if isinstance(val, list):
                        needed.update(str(v) for v in val)
                    elif val is not None:
                        needed.add(str(val))
            user_map = await self._resolve_user_ids(needed) if needed else {}
            items = [
                ListItem(
                    id=i,
                    fields=self._merge_person_fields(raw, person_names, user_map),
                )
                for i, raw in raw_items
            ]
        else:
            items = [ListItem(id=i, fields=raw) for i, raw in raw_items]

        self._cache.set(cache_key, items)
        return items


async def create_sharepoint_service(
    auth_service: Any,
    settings: Any,
) -> SharePointService:
    """Resolve site ID from URL and return a configured SharePointService."""
    client = auth_service.get_client()
    parsed = urlparse(settings.sharepoint_site_url)
    hostname = parsed.netloc
    site_path = parsed.path.rstrip("/")
    site = await client.sites.by_site_id(f"{hostname}:{site_path}").get()
    if not site or not site.id:
        raise ValueError(
            f"Could not resolve site ID for URL: {settings.sharepoint_site_url}"
        )
    return SharePointService(
        client=client,
        site_id=site.id,
        list_id=settings.sharepoint_list_id,
        cache_ttl=settings.cache_ttl_seconds,
    )
