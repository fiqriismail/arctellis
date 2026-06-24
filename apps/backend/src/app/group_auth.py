from __future__ import annotations

import time

from msgraph.generated.users.item.check_member_objects.check_member_objects_post_request_body import (
    CheckMemberObjectsPostRequestBody,
)

from app.services.graph_auth import GraphAuthService

# Module-level cache singleton — shared across requests
_cache: GroupMembershipCache


class GroupMembershipCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[bool, float]] = {}

    def get(self, oid: str) -> bool | None:
        entry = self._store.get(oid)
        if entry is None:
            return None
        result, expiry = entry
        if time.time() >= expiry:
            del self._store[oid]
            return None
        return result

    def set(self, oid: str, result: bool) -> None:
        self._store[oid] = (result, time.time() + self._ttl)


_cache = GroupMembershipCache(ttl_seconds=300)


async def check_group_membership(
    oid: str,
    group_id: str,
    auth_service: GraphAuthService,
) -> bool:
    """Call Graph checkMemberObjects and return True if oid is in group_id.

    Raises on any Graph error — callers should handle and return 503.
    """
    client = auth_service.get_client()
    body = CheckMemberObjectsPostRequestBody(ids=[group_id])
    response = await client.users.by_user_id(oid).check_member_objects.post(body)
    return group_id in (response.value or [])
