import asyncio

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY
from gamerhq_skill_awin_affiliate.campaigns import CAMPAIGNS_KEY, CAMPAIGN_HISTORY_KEY, Campaign
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState
from gamerhq_skill_awin_affiliate.setup import ACCESS_TOKEN_SECRET, SETTINGS_KEY


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
    async def write(self, **kwargs):
        return None


class Http:
    async def request(self, **kwargs):
        raise AssertionError("Diagnostics must not call Awin over HTTP.")


class Context:
    def __init__(self):
        self.guild_id = 123
        self.storage = Storage()
        self.secrets = Secrets()
        self.audit = Audit()
        self.http = Http()


def creative(id, *, state=CreativeState.ACTIVE, enabled=True):
    return Creative(
        id=id,
        provider="awin",
        publisher_id="20",
        advertiser_id="10",
        external_creative_id=id,
        creative_group_id=None,
        advertiser_name="Advertiser",
        type="image",
        image_url=f"https://www.awin1.com/cshow.php?s={id}",
        tracking_url=f"https://www.awin1.com/cread.php?s={id}",
        state=state,
        user_enabled=enabled,
    )


def test_management_diagnostics_never_exposes_token_or_raw_failure_text():
    async def run():
        ctx = Context()
        secret = "super-secret-awin-token"
        raw_failure = "private stack trace with secret material"
        ctx.secrets.values[ACCESS_TOKEN_SECRET] = secret
        ctx.storage.values[SETTINGS_KEY] = {
            "schemaVersion": 1,
            "publisherId": "20",
            "publisherName": "GamerHQ",
        }
        ctx.storage.values[STORAGE_KEY] = [
            creative("a").to_dict(),
            creative("b", state=CreativeState.MISSING, enabled=False).to_dict(),
        ]
        ctx.storage.values[CAMPAIGNS_KEY] = [
            Campaign(
                id="campaign-1",
                name="Deals",
                advertiser_id="10",
                channel_id=50,
                selected_creative_ids=("a",),
                rotation="fixed",
                interval_seconds=10800,
                blocked_reason="No enabled active Creative is available.",
            ).to_dict()
        ]
        ctx.storage.values[CAMPAIGN_HISTORY_KEY] = [
            {
                "campaignId": "campaign-1",
                "outcome": "failed",
                "occurredAt": 100,
                "creativeId": "a",
                "channelId": 50,
                "messageId": None,
                "reason": "discord-send-failed",
            }
        ]

        result = await AwinAffiliateSkill()._manage_diagnostics(ctx, {})
        payload = result["diagnostics"]
        serialized = repr(payload)

        assert payload["setup"]["connected"] is True
        assert payload["setup"]["tokenStored"] is True
        assert payload["setup"]["publisher"] == {"id": "20", "name": "GamerHQ"}
        assert secret not in serialized
        assert "••••••••" not in serialized
        assert raw_failure not in serialized
        assert payload["deliveryHistory"]["failed"] == 1
        assert payload["campaigns"]["blocked"] == 1

    asyncio.run(run())


def test_health_detail_reports_blocked_campaign_count_without_token():
    async def run():
        ctx = Context()
        ctx.secrets.values[ACCESS_TOKEN_SECRET] = "secret"
        ctx.storage.values[SETTINGS_KEY] = {
            "schemaVersion": 1,
            "publisherId": "20",
            "publisherName": "GamerHQ",
        }
        ctx.storage.values[STORAGE_KEY] = [creative("a").to_dict()]
        ctx.storage.values[CAMPAIGNS_KEY] = [
            Campaign(
                id="campaign-1",
                name="Deals",
                advertiser_id="10",
                channel_id=50,
                selected_creative_ids=("a",),
                rotation="fixed",
                interval_seconds=10800,
                blocked_reason="No enabled active Creative is available.",
            ).to_dict()
        ]

        health = await AwinAffiliateSkill().health_check(ctx)

        assert health.state == "PASS"
        assert "1 blocked campaign(s)" in health.detail
        assert "secret" not in health.detail

    asyncio.run(run())
