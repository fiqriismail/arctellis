from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
