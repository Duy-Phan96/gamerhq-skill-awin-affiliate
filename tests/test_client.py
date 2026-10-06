import asyncio
import json

import pytest

from gamerhq_skill_awin_affiliate.client import AwinApiClient, AwinApiError


class Response:
    def __init__(self, status, payload):
        self.status = status
        self.body = json.dumps(payload)

    def json(self):
        return json.loads(self.body)


class Http:
    def __init__(self, response):
        self.response = response

    async def request(self, **kwargs):
        return self.response


def test_accounts_ignore_non_publishers_and_deduplicate():
    async def run():
        response = Response(
            200,
            {
                "accounts": [
                    {"accountId": 2, "accountName": "B", "accountType": "publisher"},
                    {"accountId": 1, "accountName": "A", "accountType": "publisher"},
                    {"accountId": 1, "accountName": "Duplicate", "accountType": "publisher"},
                    {"accountId": 3, "accountName": "Advertiser", "accountType": "advertiser"},
                ]
            },
        )
        result = await AwinApiClient(Http(response)).publisher_accounts(access_token="token")
        assert [(item.id, item.name) for item in result] == [("1", "A"), ("2", "B")]

    asyncio.run(run())


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (403, "rejected"),
        (429, "rate limit"),
        (503, "temporarily unavailable"),
    ],
)
def test_accounts_map_provider_errors_to_safe_messages(status, message):
    async def run():
        with pytest.raises(AwinApiError, match=message):
            await AwinApiClient(Http(Response(status, {"error": "private detail"}))).publisher_accounts(
                access_token="token"
            )

    asyncio.run(run())


def test_accounts_reject_malformed_response():
    async def run():
        with pytest.raises(AwinApiError, match="unexpected"):
            await AwinApiClient(Http(Response(200, {"wrong": []}))).publisher_accounts(
                access_token="token"
            )

    asyncio.run(run())
