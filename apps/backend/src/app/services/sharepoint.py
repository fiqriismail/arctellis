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
    lookup_list_id: str | None = None
    lookup_column_name: str | None = None


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
        # Resolved list lookup entries: {list_id: {item_id: {LookupValue}}}.
        self._lookup_cache: dict[str, dict[str, dict]] = {}

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
            lookup_list_id = None
            lookup_column_name = None
            if col.lookup is not None:
                lookup_list_id = col.lookup.list_id
                lookup_column_name = col.lookup.column_name
            columns.append(
                ColumnDefinition(
                    name=col.name,
                    display_name=col.display_name or col.name,
                    column_type=self._infer_column_type(col),
                    lookup_list_id=lookup_list_id,
                    lookup_column_name=lookup_column_name,
                )
            )
        self._cache.set("schema", columns)
        return columns

    async def _person_field_names(self) -> set[str]:
        """Internal names of columns whose type is 'person', from the schema."""
        columns = await self.get_schema()
        return {c.name for c in columns if c.column_type == "person"}

    async def _lookup_field_configs(self) -> dict[str, tuple[str, str]]:
        """Internal names of resolvable lookup columns -> (list_id, column_name).

        Only includes lookups backed by a real SharePoint list GUID (e.g. Category
        taxonomy). Skips system lookups such as FolderChildCount and AppPrincipals.
        """
        columns = await self.get_schema()
        configs: dict[str, tuple[str, str]] = {}
        for col in columns:
            if col.column_type != "lookup" or not col.lookup_list_id:
                continue
            if "-" not in col.lookup_list_id:
                continue
            configs[col.name] = (
                col.lookup_list_id,
                col.lookup_column_name or "Title",
            )
        return configs

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

    async def _resolve_lookup_ids(
        self,
        list_id: str,
        ids: set[str],
        column_name: str = "Title",
    ) -> dict[str, dict]:
        """Resolve lookup item ids in a target list to {LookupValue}."""
        if list_id not in self._lookup_cache:
            self._lookup_cache[list_id] = {}
        cache = self._lookup_cache[list_id]
        resolved: dict[str, dict] = {}
        for lid in ids:
            if lid in cache:
                resolved[lid] = cache[lid]
                continue
            try:
                item = await (
                    self._client.sites.by_site_id(self._site_id)
                    .lists.by_list_id(list_id)
                    .items.by_list_item_id(lid)
                    .get()
                )
                ad = item.fields.additional_data if item and item.fields else {}
                title = (
                    ad.get("CategoryDisplayName")
                    or ad.get(column_name)
                    or ad.get("Title")
                )
                info = {"LookupValue": title}
            except Exception:
                logger.warning(
                    "Could not resolve lookup id %s in list %s", lid, list_id
                )
                info = {"LookupValue": None}
            cache[lid] = info
            resolved[lid] = info
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
    def _merge_lookup_fields(
        fields: dict[str, Any],
        lookup_configs: dict[str, tuple[str, str]],
        lookup_maps: dict[str, dict[str, dict]],
    ) -> dict[str, Any]:
        """Replace '{Lookup}LookupId' keys with resolved {LookupValue}.

        Pure function: given raw fields, lookup column configs, and per-list id
        maps, return fields with each lookup column populated under its internal
        name and the raw LookupId key removed.
        """
        unresolved = {"LookupValue": None}
        out = dict(fields)
        for name, (list_id, _) in lookup_configs.items():
            key = f"{name}LookupId"
            if key not in out:
                continue
            raw = out.pop(key)
            id_map = lookup_maps.get(list_id, {})
            if isinstance(raw, list):
                out[name] = [id_map.get(str(i), unresolved) for i in raw]
            else:
                out[name] = id_map.get(str(raw), unresolved)
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

    async def get_item_count(self) -> int:
        """Return the total number of items in the list.

        Fetches item IDs only (no field expansion) since the Graph API does
        not support $count on the list items endpoint. Result is cached.
        """
        cache_key = "count:"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        builder = items_request_builder.ItemsRequestBuilder
        query_params = builder.ItemsRequestBuilderGetQueryParameters(
            select=["id"], top=5000
        )
        request_configuration = RequestConfiguration(query_parameters=query_params)
        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .items.get(request_configuration=request_configuration)
        )
        count = len(result.value) if result and result.value else 0
        self._cache.set(cache_key, count)
        return count

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
        if odata_filter:
            # SharePoint rejects filters on non-indexed columns unless this
            # header is present. The list is small (well under the row
            # threshold), so the "may fail randomly" caveat does not apply.
            request_configuration.headers.add(
                "Prefer", "HonorNonIndexedQueriesWarningMayFailRandomly"
            )

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
            lookup_configs = await self._lookup_field_configs()
            needed_users: set[str] = set()
            needed_lookups: dict[str, set[str]] = {}
            for _, raw in raw_items:
                for name in person_names:
                    val = raw.get(f"{name}LookupId")
                    if isinstance(val, list):
                        needed_users.update(str(v) for v in val)
                    elif val is not None:
                        needed_users.add(str(val))
                for name, (list_id, _) in lookup_configs.items():
                    val = raw.get(f"{name}LookupId")
                    if isinstance(val, list):
                        needed_lookups.setdefault(list_id, set()).update(
                            str(v) for v in val
                        )
                    elif val is not None:
                        needed_lookups.setdefault(list_id, set()).add(str(val))
            user_map = await self._resolve_user_ids(needed_users) if needed_users else {}
            lookup_maps: dict[str, dict[str, dict]] = {}
            for list_id, ids in needed_lookups.items():
                column_name = next(
                    col
                    for _, (lid, col) in lookup_configs.items()
                    if lid == list_id
                )
                lookup_maps[list_id] = await self._resolve_lookup_ids(
                    list_id, ids, column_name
                )
            items = [
                ListItem(
                    id=i,
                    fields=self._merge_lookup_fields(
                        self._merge_person_fields(raw, person_names, user_map),
                        lookup_configs,
                        lookup_maps,
                    ),
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
