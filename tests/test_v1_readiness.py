import asyncio

import pytest

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY
from gamerhq_skill_awin_affiliate.campaigns import CAMPAIGNS_KEY, Campaign
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState


class Storage:
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


class Scheduler:
    def __init__(self):
        self.jobs = {}

    async def upsert_job(self, **kwargs):
        self.jobs[kwargs["key"]] = kwargs

    async def remove_job(self, *, key):
        self.jobs.pop(key, None)


class Discord:
    async def get_channel(self, *, channel_id):
        return type("Channel", (), {"id": channel_id, "name": "deals", "kind": "text"})()

    async def send_message(self, **kwargs):
        return 999


class Context:
    def __init__(self):
        self.guild_id = 123
        self.storage = Storage()
        self.audit = Audit()
        self.scheduler = Scheduler()
        self.discord = Discord()


def creative(creative_id="a", *, state=CreativeState.ACTIVE, enabled=True):
    return Creative(
        id=creative_id,
        provider="awin",
        publisher_id="20",
        advertiser_id="10",
        external_creative_id=creative_id,
        creative_group_id=None,
        advertiser_name="Advertiser",
        type="image",
        image_url=f"https://www.awin1.com/cshow.php?s={creative_id}",
        tracking_url=f"https://www.awin1.com/cread.php?s={creative_id}",
        state=state,
        user_enabled=enabled,
    )


def campaign_dict(**changes):
    value = {
        "id": "campaign-1",
        "name": "Deals",
        "advertiserId": "10",
        "channelId": 50,
        "selectedCreativeIds": ["a"],
        "rotation": "fixed",
        "intervalSeconds": 3600,
        "enabled": True,
        "avoidImmediateRepeat": True,
        "lastCreativeId": None,
        "sequentialIndex": 0,
        "shuffleRemaining": [],
        "blockedReason": None,
    }
    value.update(changes)
    return value


def test_campaign_create_rejects_string_boolean_values():
    async def run():
        ctx = Context()
        ctx.storage.values[STORAGE_KEY] = [creative().to_dict()]
        skill = AwinAffiliateSkill()

        with pytest.raises(ValueError, match="must be booleans"):
            await skill._manage_campaign_create(
                ctx,
                {
                    "name": "Deals",
                    "advertiserId": "10",
                    "channelId": 50,
                    "selectedCreativeIds": ["a"],
                    "rotation": "fixed",
                    "intervalSeconds": 3600,
                    "enabled": "false",
                    "avoidImmediateRepeat": True,
                },
            )

        assert CAMPAIGNS_KEY not in ctx.storage.values

    asyncio.run(run())


@pytest.mark.parametrize(
    "field,value",
    [
        ("enabled", "false"),
        ("avoidImmediateRepeat", 1),
    ],
)
def test_campaign_from_dict_rejects_non_boolean_persisted_values(field, value):
    with pytest.raises(ValueError, match="Stored Awin campaign is invalid"):
        Campaign.from_dict(campaign_dict(**{field: value}))


def test_creative_from_dict_rejects_non_boolean_user_enabled():
    value = creative().to_dict()
    value["userEnabled"] = "false"

    with pytest.raises(ValueError, match="Stored Awin creative is invalid"):
        Creative.from_dict(value)


def test_recovered_creative_clears_stale_blocked_status_in_management_view():
    async def run():
        ctx = Context()
        ctx.storage.values[STORAGE_KEY] = [creative().to_dict()]
        ctx.storage.values[CAMPAIGNS_KEY] = [
            campaign_dict(blockedReason="No enabled active Creative is available.")
        ]
        skill = AwinAffiliateSkill()

        detail = await skill._manage_campaign_get(
            ctx,
            {"campaignId": "campaign-1"},
        )
        listing = await skill._manage_campaign_list(ctx, {})

        assert detail["campaign"]["status"] == "active"
        assert detail["campaign"]["blockedReason"] is None
        assert detail["campaign"]["eligibleCreativeCount"] == 1
        assert listing["campaigns"][0]["status"] == "active"
        assert listing["campaigns"][0]["blockedReason"] is None

    asyncio.run(run())


def test_campaign_list_derives_blocked_status_from_current_eligibility():
    async def run():
        ctx = Context()
        ctx.storage.values[STORAGE_KEY] = [
            creative(state=CreativeState.MISSING).to_dict()
        ]
        ctx.storage.values[CAMPAIGNS_KEY] = [campaign_dict(blockedReason=None)]
        skill = AwinAffiliateSkill()

        listing = await skill._manage_campaign_list(ctx, {})

        campaign = listing["campaigns"][0]
        assert campaign["status"] == "blocked"
        assert campaign["eligibleCreativeCount"] == 0
        assert campaign["blockedReason"] == "No enabled active Creative is available."

    asyncio.run(run())
