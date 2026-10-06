import asyncio
import json

import pytest

from gamerhq_skill_awin_affiliate import (
    ACCESS_TOKEN_SECRET_KEY,
    CONNECTION_STORAGE_KEY,
    AwinAffiliateSkill,
    ConnectionStatus,
)
from gamerhq_skill_awin_affiliate.client import AwinApiError


class Response:
    def __init__(self, status, payload):
        self.status = status
        self.headers = {"content-type": "application/json"}
        self.body = json.dumps(payload)

    def json(self):
        return json.loads(self.body)


class Http:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def request(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class Storage:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value):
        self.values[key] = value

    async def delete(self, key):
        self.values.pop(key, None)


class Secrets:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value):
        self.values[key] = value

    async def delete(self, key):
        self.values.pop(key, None)


class Audit:
    def __init__(self):
        self.calls = []

    async def write(self, **kwargs):
        self.calls.append(kwargs)


class Context:
    def __init__(self, response):
        self.storage = Storage()
        self.secrets = Secrets()
        self.http = Http(response)
        self.audit = Audit()


def accounts(*items):
    return {
        "userId": 77,
        "accounts": [
            {
                "accountId": account_id,
                "accountName": name,
                "accountType": "publisher",
                "userRole": role,
            }
            for account_id, name, role in items
        ],
    }


def test_single_publisher_is_auto_selected_and_token_is_secret_only():
    async def run():
        ctx = Context(Response(200, accounts((123, "Publisher One", "owner"))))
        skill = AwinAffiliateSkill()

        connection = await skill.connect(ctx, access_token="test-access-token", now=100)

        assert connection.status == ConnectionStatus.CONNECTED
        assert connection.publisher_id == "123"
        assert connection.publisher_name == "Publisher One"
        assert ctx.secrets.values[ACCESS_TOKEN_SECRET_KEY] == "test-access-token"
        assert "test-access-token" not in json.dumps(ctx.storage.values)
        assert ctx.storage.values[CONNECTION_STORAGE_KEY]["publisherId"] == "123"

        request = ctx.http.calls[0]
        assert request["method"] == "GET"
        assert request["url"] == "https://api.awin.com/accounts"
        assert request["query"] == {"type": "publisher"}
        assert request["headers"]["Authorization"] == "Bearer test-access-token"

    asyncio.run(run())


def test_multiple_publishers_require_selection_then_revalidate():
    async def run():
        ctx = Context(
            Response(
                200,
                accounts(
                    (200, "Second Publisher", "member"),
                    (100, "First Publisher", "owner"),
                ),
            )
        )
        skill = AwinAffiliateSkill()

        pending = await skill.connect(ctx, access_token="token-value", now=100)
        assert pending.status == ConnectionStatus.PUBLISHER_SELECTION_REQUIRED
        assert [item["publisherId"] for item in pending.available_publishers] == ["100", "200"]
        assert pending.publisher_id is None

        selected = await skill.select_publisher(ctx, publisher_id="200", now=200)
        assert selected.status == ConnectionStatus.CONNECTED
        assert selected.publisher_id == "200"
        assert selected.publisher_name == "Second Publisher"
        assert len(ctx.http.calls) == 2
        assert ctx.secrets.values[ACCESS_TOKEN_SECRET_KEY] == "token-value"

    asyncio.run(run())


def test_invalid_selected_publisher_does_not_store_token():
    async def run():
        ctx = Context(Response(200, accounts((123, "Publisher One", "owner"))))
        skill = AwinAffiliateSkill()

        with pytest.raises(ValueError, match="not available"):
            await skill.connect(
                ctx,
                access_token="must-not-persist",
                publisher_id="999",
                now=100,
            )

        assert ACCESS_TOKEN_SECRET_KEY not in ctx.secrets.values
        assert CONNECTION_STORAGE_KEY not in ctx.storage.values

    asyncio.run(run())


def test_rejected_token_is_not_persisted():
    async def run():
        ctx = Context(Response(401, {"error": "unauthorized"}))
        skill = AwinAffiliateSkill()

        with pytest.raises(AwinApiError, match="rejected"):
            await skill.connect(ctx, access_token="bad-token", now=100)

        assert ctx.secrets.values == {}
        assert ctx.storage.values == {}

    asyncio.run(run())


def test_connection_view_never_returns_token():
    async def run():
        ctx = Context(Response(200, accounts((123, "Publisher One", "owner"))))
        skill = AwinAffiliateSkill()
        await skill.connect(ctx, access_token="private-token", now=100)

        view = await skill.connection_view(ctx)
        encoded = json.dumps(view)

        assert view["tokenConfigured"] is True
        assert view["connectionReady"] is True
        assert "private-token" not in encoded
        assert "accessToken" not in view

    asyncio.run(run())


def test_disconnect_removes_token_and_connection_metadata():
    async def run():
        ctx = Context(Response(200, accounts((123, "Publisher One", "owner"))))
        skill = AwinAffiliateSkill()
        await skill.connect(ctx, access_token="private-token", now=100)

        await skill.disconnect(ctx)

        assert await ctx.secrets.get(ACCESS_TOKEN_SECRET_KEY) is None
        assert await ctx.storage.get(CONNECTION_STORAGE_KEY) is None
        assert ctx.audit.calls[-1]["action"] == "account.disconnected"

    asyncio.run(run())
