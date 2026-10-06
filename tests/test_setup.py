import asyncio
import json

import pytest
from skill_runtime import ExternalHttpResponse

from gamerhq_skill_awin_affiliate.awin_api import AwinApiError
from gamerhq_skill_awin_affiliate.setup import (
    ACCESS_TOKEN_SECRET,
    SETTINGS_KEY,
    AwinSetupService,
)


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


class Http:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def request(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class Context:
    def __init__(self, responses):
        self.storage = Storage()
        self.secrets = Secrets()
        self.audit = Audit()
        self.http = Http(responses)


def response(payload, status=200):
    return ExternalHttpResponse(
        status=status,
        headers={"content-type": "application/json"},
        body=json.dumps(payload),
    )


def test_connect_auto_selects_single_publisher_and_masks_token():
    async def run():
        ctx = Context([
            response([
                {
                    "accountId": 3095707,
                    "accountName": "GamerHQ",
                    "accountType": "publisher",
                    "userRole": "admin",
                }
            ])
        ])
        setup = AwinSetupService(ctx)

        result = await setup.connect(token="top-secret-token")
        status = await setup.status()

        assert result["selectionRequired"] is False
        assert result["publisher"] == {"id": "3095707", "name": "GamerHQ"}
        assert ctx.secrets.values[ACCESS_TOKEN_SECRET] == "top-secret-token"
        assert ctx.storage.values[SETTINGS_KEY]["publisherId"] == "3095707"
        assert status["token"] == "••••••••"
        assert "top-secret-token" not in str(result)
        assert ctx.http.calls[0]["headers"]["Authorization"] == "Bearer top-secret-token"

    asyncio.run(run())


def test_connect_multiple_publishers_requires_selection():
    async def run():
        ctx = Context([
            response([
                {"accountId": 1, "accountName": "One", "accountType": "publisher"},
                {"accountId": 2, "accountName": "Two", "accountType": "publisher"},
            ])
        ])
        result = await AwinSetupService(ctx).connect(token="secret")

        assert result["selectionRequired"] is True
        assert result["publisher"] is None
        assert [item["id"] for item in result["accounts"]] == ["1", "2"]

    asyncio.run(run())


def test_invalid_token_is_not_persisted():
    async def run():
        ctx = Context([response({"error": "unauthorized"}, status=401)])
        ctx.secrets.values[ACCESS_TOKEN_SECRET] = "old-token"

        with pytest.raises(AwinApiError, match="rejected"):
            await AwinSetupService(ctx).connect(token="bad-token")

        assert ctx.secrets.values[ACCESS_TOKEN_SECRET] == "old-token"

    asyncio.run(run())


def test_select_publisher_revalidates_against_connected_account():
    async def run():
        ctx = Context([
            response([
                {"accountId": 1, "accountName": "One", "accountType": "publisher"},
                {"accountId": 2, "accountName": "Two", "accountType": "publisher"},
            ])
        ])
        ctx.secrets.values[ACCESS_TOKEN_SECRET] = "secret"

        result = await AwinSetupService(ctx).select_publisher(publisher_id="2")

        assert result["publisher"] == {"id": "2", "name": "Two"}
        assert ctx.storage.values[SETTINGS_KEY]["publisherId"] == "2"

    asyncio.run(run())


def test_programme_discovery_uses_selected_publisher():
    async def run():
        ctx = Context([
            response([
                {
                    "id": 129591,
                    "name": "Ugovaper",
                    "status": "active",
                    "relationship": "joined",
                    "currencyCode": "EUR",
                    "primaryRegion": {"countryCode": "DE", "name": "Germany"},
                }
            ])
        ])
        ctx.secrets.values[ACCESS_TOKEN_SECRET] = "secret"
        ctx.storage.values[SETTINGS_KEY] = {
            "schemaVersion": 1,
            "publisherId": "3095707",
            "publisherName": "GamerHQ",
        }

        programmes = await AwinSetupService(ctx).programmes(relationship="joined")

        assert programmes[0].id == "129591"
        assert programmes[0].name == "Ugovaper"
        assert ctx.http.calls[0]["url"].endswith("/publishers/3095707/programmes")
        assert ctx.http.calls[0]["query"] == {"relationship": "joined"}

    asyncio.run(run())


def test_disconnect_deletes_token_and_publisher_selection():
    async def run():
        ctx = Context([])
        ctx.secrets.values[ACCESS_TOKEN_SECRET] = "secret"
        ctx.storage.values[SETTINGS_KEY] = {
            "schemaVersion": 1,
            "publisherId": "1",
            "publisherName": "One",
        }

        await AwinSetupService(ctx).disconnect()

        assert ACCESS_TOKEN_SECRET not in ctx.secrets.values
        assert ctx.storage.values[SETTINGS_KEY]["publisherId"] is None

    asyncio.run(run())
