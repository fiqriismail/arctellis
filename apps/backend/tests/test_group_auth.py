import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Cache unit tests ──────────────────────────────────────────────────────────


def test_cache_miss_returns_none():
    from app.group_auth import GroupMembershipCache

    cache = GroupMembershipCache(ttl_seconds=300)
    assert cache.get("unknown-oid") is None


def test_cache_hit_returns_stored_value():
    from app.group_auth import GroupMembershipCache

    cache = GroupMembershipCache(ttl_seconds=300)
    cache.set("oid-1", True)
    assert cache.get("oid-1") is True


def test_cache_stores_false():
    from app.group_auth import GroupMembershipCache

    cache = GroupMembershipCache(ttl_seconds=300)
    cache.set("oid-2", False)
    assert cache.get("oid-2") is False


def test_cache_entry_expires_after_ttl():
    from app.group_auth import GroupMembershipCache

    cache = GroupMembershipCache(ttl_seconds=1)
    cache.set("oid-3", True)

    # Advance time past TTL
    with patch("app.group_auth.time") as mock_time:
        mock_time.time.return_value = time.time() + 2
        assert cache.get("oid-3") is None


# ── check_group_membership unit tests ────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_group_membership_returns_true_when_member():
    from app.group_auth import check_group_membership
    from app.services.graph_auth import GraphAuthService

    auth = MagicMock(spec=GraphAuthService)
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.value = ["group-abc"]
    mock_client.users.by_user_id.return_value.check_member_objects.post = AsyncMock(
        return_value=mock_response
    )
    auth.get_client.return_value = mock_client

    result = await check_group_membership("oid-1", "group-abc", auth)
    assert result is True


@pytest.mark.asyncio
async def test_check_group_membership_returns_false_when_not_member():
    from app.group_auth import check_group_membership
    from app.services.graph_auth import GraphAuthService

    auth = MagicMock(spec=GraphAuthService)
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.value = []
    mock_client.users.by_user_id.return_value.check_member_objects.post = AsyncMock(
        return_value=mock_response
    )
    auth.get_client.return_value = mock_client

    result = await check_group_membership("oid-1", "group-abc", auth)
    assert result is False


@pytest.mark.asyncio
async def test_check_group_membership_raises_on_graph_error():
    from app.group_auth import check_group_membership
    from app.services.graph_auth import GraphAuthService

    auth = MagicMock(spec=GraphAuthService)
    mock_client = MagicMock()
    mock_client.users.by_user_id.return_value.check_member_objects.post = AsyncMock(
        side_effect=Exception("Graph API unavailable")
    )
    auth.get_client.return_value = mock_client

    with pytest.raises(Exception, match="Graph API unavailable"):
        await check_group_membership("oid-1", "group-abc", auth)
