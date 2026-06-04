from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from msgraph import GraphServiceClient


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
