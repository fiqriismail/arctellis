from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.sites.item.lists.item.items import items_request_builder


@dataclass
class ColumnDefinition:
    name: str
    display_name: str
    column_type: str  # "text" | "number" | "dateTime" | "choice" | "boolean" | "lookup" | "person" | "other"


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
    ) -> None:
        self._client = client
        self._site_id = site_id
        self._list_id = list_id

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
        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .columns.get()
        )
        columns: list[ColumnDefinition] = []
        if not result or not result.value:
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
        return columns

    async def get_items(self, odata_filter: str | None = None) -> list[ListItem]:
        query_params = items_request_builder.ItemsRequestBuilder.ItemsRequestBuilderGetQueryParameters(
            expand=["fields"],
        )
        if odata_filter:
            query_params.filter = odata_filter

        request_configuration = RequestConfiguration(query_parameters=query_params)

        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .items.get(request_configuration=request_configuration)
        )

        # Note: only fetches first page (~200 items). Pagination via odata_next_link not implemented.
        items: list[ListItem] = []
        if not result or not result.value:
            return items

        for item in result.value:
            fields: dict[str, Any] = {}
            if item.fields and item.fields.additional_data:
                fields = dict(item.fields.additional_data)
            items.append(ListItem(id=item.id or "", fields=fields))

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
        raise ValueError(f"Could not resolve site ID for URL: {settings.sharepoint_site_url}")
    return SharePointService(
        client=client,
        site_id=site.id,
        list_id=settings.sharepoint_list_id,
    )
