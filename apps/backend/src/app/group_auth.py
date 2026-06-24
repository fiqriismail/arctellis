from __future__ import annotations

import time

from msgraph.generated.models.o_data_errors.o_data_error import ODataError

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
    """Return True if oid is a transitive member of group_id.

    Uses GET /users/{oid}/transitiveMemberOf/{groupId}: 200 = member, 404 = not member.
    Requires GroupMember.Read.All Application permission (not Directory.Read.All).
    Raises on non-404 Graph errors — callers should return 503.
    """
    client = auth_service.get_client()
    try:
        await client.users.by_user_id(oid).transitive_member_of.by_directory_object_id(group_id).get()
        return True
    except ODataError as e:
        if e.response_status_code == 404:
            return False
        raise
