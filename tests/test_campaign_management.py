import asyncio
from types import SimpleNamespace

import pytest

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY
from gamerhq_skill_awin_affiliate.campaigns import CAMPAIGNS_KEY, CAMPAIGN_HANDLER_ID
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
    def __init__(self):
        self.calls = []

    async def write(self, **kwargs):
        self.calls.append(kwargs)


class Scheduler:
    def __init__(self):
        self.jobs = {}
        self.removed = []

    async def upsert_job(self, **kwargs):
        self.jobs[kwargs["key"]] = kwargs

    async def remove_job(self, *, key):
        self.jobs.pop(key, None)
        self.removed.append(key)


class Discord:
    def __init__(self):
        self.sent = []
        self.fail_send = False

    async def get_channel(self, *, channel_id):
        return SimpleNamespace(id=channel_id, name="deals", kind="text")

    async def send_message(self, **kwargs):
        if self.fail_send:
            raise RuntimeError("synthetic send failure")
        self.sent.append(kwargs)
        return 9001


class Context:
    def __init__(self):
        self.guild_id = 123
        self.storage = Storage()
        self.audit = Audit()
        self.scheduler = Scheduler()
        self.discord = Discord()


def creative(id):
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
        state=CreativeState.ACTIVE,
        user_enabled=True,
    )


def seed(ctx, *items):
    ctx.storage.values[STORAGE_KEY] = [item.to_dict() for item in items]


def test_campaign_create_schedules_pause_resume_delete():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b"))
        skill = AwinAffiliateSkill()

        created = await skill._manage_campaign_create(
            ctx,
            {
                "name": "Deals",
                "advertiserId": "10",
                "channelId": 50,
                "selectedCreativeIds": ["a", "b"],
                "rotation": "shuffle",
                "intervalSeconds": 10800,
            },
        )
        campaign = created["campaign"]
        key = f"campaign:{campaign['id']}"
        assert key in ctx.scheduler.jobs
        assert ctx.scheduler.jobs[key]["handler_id"] == CAMPAIGN_HANDLER_ID
        assert ctx.scheduler.jobs[key]["schedule"] == {"type": "interval", "seconds": 10800}

        paused = await skill._manage_campaign_set_active(
            ctx, {"campaignId": campaign["id"], "active": False}
        )
        assert paused["campaign"]["enabled"] is False
        assert key not in ctx.scheduler.jobs

        resumed = await skill._manage_campaign_set_active(
            ctx, {"campaignId": campaign["id"], "active": True}
        )
        assert resumed["campaign"]["enabled"] is True
        assert key in ctx.scheduler.jobs

        deleted = await skill._manage_campaign_delete(
            ctx, {"campaignId": campaign["id"]}
        )
        assert deleted["deleted"] is True
        assert ctx.storage.values[CAMPAIGNS_KEY] == []
        assert key not in ctx.scheduler.jobs

    asyncio.run(run())


def test_campaign_run_now_sends_and_advances_sequential_rotation():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b"))
        skill = AwinAffiliateSkill()
        created = await skill._manage_campaign_create(
            ctx,
            {
                "name": "Deals",
                "advertiserId": "10",
                "channelId": 50,
                "selectedCreativeIds": ["a", "b"],
                "rotation": "sequential",
                "intervalSeconds": 10800,
            },
        )
        cid = created["campaign"]["id"]

        first = await skill._manage_campaign_run_now(ctx, {"campaignId": cid})
        second = await skill._manage_campaign_run_now(ctx, {"campaignId": cid})

        assert [first["creativeId"], second["creativeId"]] == ["a", "b"]
        assert len(ctx.discord.sent) == 2
        assert "Werbung · Affiliate-Link" in ctx.discord.sent[0]["content"]

    asyncio.run(run())


def test_failed_send_does_not_advance_campaign_rotation():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b"))
        skill = AwinAffiliateSkill()
        created = await skill._manage_campaign_create(
            ctx,
            {
                "name": "Deals",
                "advertiserId": "10",
                "channelId": 50,
                "selectedCreativeIds": ["a", "b"],
                "rotation": "sequential",
                "intervalSeconds": 10800,
            },
        )
        cid = created["campaign"]["id"]
        ctx.discord.fail_send = True

        with pytest.raises(RuntimeError, match="synthetic"):
            await skill._manage_campaign_run_now(ctx, {"campaignId": cid})

        ctx.discord.fail_send = False
        result = await skill._manage_campaign_run_now(ctx, {"campaignId": cid})
        assert result["creativeId"] == "a"

    asyncio.run(run())


def test_campaign_blocks_when_selected_creatives_become_unavailable():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"))
        skill = AwinAffiliateSkill()
        created = await skill._manage_campaign_create(
            ctx,
            {
                "name": "Deals",
                "advertiserId": "10",
                "channelId": 50,
                "selectedCreativeIds": ["a"],
                "rotation": "fixed",
                "intervalSeconds": 10800,
            },
        )
        cid = created["campaign"]["id"]
        missing = creative("a")
        missing = Creative.from_dict({**missing.to_dict(), "state": "MISSING"})
        seed(ctx, missing)

        result = await skill._manage_campaign_run_now(ctx, {"campaignId": cid})
        assert result["sent"] is False
        assert result["blocked"] is True
        assert ctx.discord.sent == []

    asyncio.run(run())
