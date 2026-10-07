import asyncio

import pytest

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY
from gamerhq_skill_awin_affiliate.campaigns import CAMPAIGN_HISTORY_KEY, CAMPAIGNS_KEY
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

    async def upsert_job(self, **kwargs):
        self.jobs[kwargs["key"]] = kwargs

    async def remove_job(self, *, key):
        self.jobs.pop(key, None)


class Discord:
    def __init__(self):
        self.fail = False
        self.sent = []

    async def get_channel(self, *, channel_id):
        return type("Channel", (), {"id": channel_id, "name": "deals", "kind": "text"})()

    async def send_message(self, **kwargs):
        if self.fail:
            raise RuntimeError("synthetic send failure")
        self.sent.append(kwargs)
        return 777


class Context:
    def __init__(self):
        self.guild_id = 123
        self.storage = Storage()
        self.audit = Audit()
        self.scheduler = Scheduler()
        self.discord = Discord()


def creative(id, advertiser_id="10", state=CreativeState.ACTIVE, enabled=True):
    return Creative(
        id=id,
        provider="awin",
        publisher_id="20",
        advertiser_id=advertiser_id,
        external_creative_id=id,
        creative_group_id=None,
        advertiser_name="Advertiser",
        type="image",
        image_url=f"https://www.awin1.com/cshow.php?s={id}",
        tracking_url=f"https://www.awin1.com/cread.php?s={id}",
        state=state,
        user_enabled=enabled,
    )


def seed(ctx, *items):
    ctx.storage.values[STORAGE_KEY] = [item.to_dict() for item in items]


async def create_campaign(ctx, skill, *, rotation="sequential"):
    return (
        await skill._manage_campaign_create(
            ctx,
            {
                "name": "Deals",
                "advertiserId": "10",
                "channelId": 50,
                "selectedCreativeIds": ["a", "b"],
                "rotation": rotation,
                "intervalSeconds": 10800,
            },
        )
    )["campaign"]


def test_campaign_edit_keeps_stable_id_and_reschedules():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b"))
        skill = AwinAffiliateSkill()
        created = await create_campaign(ctx, skill)
        cid = created["id"]

        updated = await skill._manage_campaign_update(
            ctx,
            {
                "campaignId": cid,
                "name": "Evening Deals",
                "channelId": 51,
                "selectedCreativeIds": ["b"],
                "rotation": "fixed",
                "intervalSeconds": 7200,
                "avoidImmediateRepeat": False,
            },
        )

        assert updated["campaign"]["id"] == cid
        assert updated["campaign"]["name"] == "Evening Deals"
        assert updated["campaign"]["rotation"] == "fixed"
        assert updated["campaign"]["selectedCreativeIds"] == ["b"]
        assert updated["campaign"]["lastCreativeId"] is None
        assert ctx.scheduler.jobs[f"campaign:{cid}"]["schedule"] == {"type": "interval", "seconds": 7200}

    asyncio.run(run())


def test_preview_next_does_not_mutate_campaign_rotation():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b"))
        skill = AwinAffiliateSkill()
        created = await create_campaign(ctx, skill)
        cid = created["id"]

        before = list(ctx.storage.values[CAMPAIGNS_KEY])
        preview = await skill._manage_campaign_preview_next(ctx, {"campaignId": cid})
        after = ctx.storage.values[CAMPAIGNS_KEY]

        assert preview["blocked"] is False
        assert preview["preview"]["creativeId"] == "a"
        assert preview["rotationMutationApplied"] is False
        assert before == after

    asyncio.run(run())


def test_campaign_get_exposes_derived_status_and_counts():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b", state=CreativeState.MISSING))
        skill = AwinAffiliateSkill()
        created = await create_campaign(ctx, skill)
        cid = created["id"]

        result = await skill._manage_campaign_get(ctx, {"campaignId": cid})

        assert result["campaign"]["status"] == "active"
        assert result["campaign"]["configuredCreativeCount"] == 2
        assert result["campaign"]["eligibleCreativeCount"] == 1

    asyncio.run(run())


def test_campaign_history_records_sent_blocked_and_failed():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b"))
        skill = AwinAffiliateSkill()
        created = await create_campaign(ctx, skill)
        cid = created["id"]

        await skill._manage_campaign_run_now(ctx, {"campaignId": cid})

        ctx.discord.fail = True
        with pytest.raises(RuntimeError, match="synthetic"):
            await skill._manage_campaign_run_now(ctx, {"campaignId": cid})

        ctx.discord.fail = False
        seed(
            ctx,
            creative("a", state=CreativeState.MISSING),
            creative("b", state=CreativeState.MISSING),
        )
        blocked = await skill._manage_campaign_run_now(ctx, {"campaignId": cid})
        assert blocked["blocked"] is True

        history = await skill._manage_campaign_history(
            ctx,
            {"campaignId": cid, "limit": 10},
        )
        outcomes = [row["outcome"] for row in history["history"]]
        assert outcomes[:3] == ["blocked", "failed", "sent"]

    asyncio.run(run())


def test_campaign_history_is_bounded_to_100_entries():
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

        for _ in range(105):
            await skill._manage_campaign_run_now(ctx, {"campaignId": cid})

        assert len(ctx.storage.values[CAMPAIGN_HISTORY_KEY]) == 100
        history = await skill._manage_campaign_history(ctx, {"campaignId": cid, "limit": 100})
        assert len(history["history"]) == 100

    asyncio.run(run())
