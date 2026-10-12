import asyncio
import copy
from types import SimpleNamespace

import pytest

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY
from gamerhq_skill_awin_affiliate.campaigns import (
    CAMPAIGNS_KEY,
    CAMPAIGN_HISTORY_KEY,
    Campaign,
)
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState


class YieldingStorage:
    """Copying storage that deliberately widens read-modify-write races."""

    def __init__(self):
        self.values = {}

    async def get(self, key):
        snapshot = copy.deepcopy(self.values.get(key))
        await asyncio.sleep(0.005)
        return snapshot

    async def set(self, key, value):
        await asyncio.sleep(0.005)
        self.values[key] = copy.deepcopy(value)

    async def delete(self, key):
        await asyncio.sleep(0.005)
        self.values.pop(key, None)


class Audit:
    def __init__(self):
        self.calls = []

    async def write(self, **kwargs):
        self.calls.append(kwargs)


class Scheduler:
    def __init__(self):
        self.jobs = {}
        self.fail_upsert = False
        self.fail_remove = False

    async def upsert_job(self, **kwargs):
        if self.fail_upsert:
            raise RuntimeError("synthetic scheduler upsert failure")
        self.jobs[kwargs["key"]] = copy.deepcopy(kwargs)

    async def remove_job(self, *, key):
        if self.fail_remove:
            raise RuntimeError("synthetic scheduler remove failure")
        self.jobs.pop(key, None)


class TwoSendBarrierDiscord:
    def __init__(self):
        self.calls = []
        self._ready = asyncio.Event()

    async def get_channel(self, *, channel_id):
        return SimpleNamespace(id=channel_id, name="deals", kind="text")

    async def send_message(self, **kwargs):
        sequence = len(self.calls) + 1
        self.calls.append(copy.deepcopy(kwargs))
        if len(self.calls) >= 2:
            self._ready.set()
        await asyncio.wait_for(self._ready.wait(), timeout=1)
        return 9000 + sequence


class BlockingDiscord:
    def __init__(self):
        self.calls = []
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def get_channel(self, *, channel_id):
        return SimpleNamespace(id=channel_id, name="deals", kind="text")

    async def send_message(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        self.started.set()
        await asyncio.wait_for(self.release.wait(), timeout=1)
        return 9100 + len(self.calls)


class Context:
    def __init__(self, *, discord):
        self.guild_id = 123
        self.storage = YieldingStorage()
        self.audit = Audit()
        self.scheduler = Scheduler()
        self.discord = discord


def creative(creative_id, *, advertiser_id):
    return Creative(
        id=creative_id,
        provider="awin",
        publisher_id="20",
        advertiser_id=advertiser_id,
        external_creative_id=creative_id,
        creative_group_id=None,
        advertiser_name=f"Advertiser {advertiser_id}",
        type="image",
        image_url=f"https://www.awin1.com/cshow.php?s={creative_id}",
        tracking_url=f"https://www.awin1.com/cread.php?s={creative_id}",
        state=CreativeState.ACTIVE,
        user_enabled=True,
    )


def campaign(campaign_id, *, advertiser_id, creative_id, name=None):
    return Campaign(
        id=campaign_id,
        name=name or campaign_id,
        advertiser_id=advertiser_id,
        channel_id=50,
        selected_creative_ids=(creative_id,),
        rotation="fixed",
        interval_seconds=900,
    )


def seed(ctx, *, creatives, campaigns):
    ctx.storage.values[STORAGE_KEY] = [item.to_dict() for item in creatives]
    ctx.storage.values[CAMPAIGNS_KEY] = [item.to_dict() for item in campaigns]
    for item in campaigns:
        ctx.scheduler.jobs[f"campaign:{item.id}"] = {
            "key": f"campaign:{item.id}",
            "handler_id": "awin-affiliate.campaign.execute.v1",
            "schedule": {"type": "interval", "seconds": item.interval_seconds},
            "payload": {"campaignId": item.id},
        }


def stored_campaigns(ctx):
    return {
        item.id: item
        for item in (
            Campaign.from_dict(row)
            for row in ctx.storage.values.get(CAMPAIGNS_KEY, [])
        )
    }


def test_parallel_campaign_runs_preserve_both_states_and_history_rows():
    async def run():
        ctx = Context(discord=TwoSendBarrierDiscord())
        seed(
            ctx,
            creatives=[
                creative("creative-a", advertiser_id="10"),
                creative("creative-b", advertiser_id="11"),
            ],
            campaigns=[
                campaign(
                    "campaign-a",
                    advertiser_id="10",
                    creative_id="creative-a",
                ),
                campaign(
                    "campaign-b",
                    advertiser_id="11",
                    creative_id="creative-b",
                ),
            ],
        )
        skill = AwinAffiliateSkill()

        results = await asyncio.gather(
            skill._manage_campaign_run_now(ctx, {"campaignId": "campaign-a"}),
            skill._manage_campaign_run_now(ctx, {"campaignId": "campaign-b"}),
        )

        assert {item["campaignId"] for item in results} == {
            "campaign-a",
            "campaign-b",
        }
        campaigns = stored_campaigns(ctx)
        assert campaigns["campaign-a"].last_creative_id == "creative-a"
        assert campaigns["campaign-b"].last_creative_id == "creative-b"

        history = ctx.storage.values[CAMPAIGN_HISTORY_KEY]
        assert len(history) == 2
        assert {row["campaignId"] for row in history} == {
            "campaign-a",
            "campaign-b",
        }
        assert {row["outcome"] for row in history} == {"sent"}

    asyncio.run(run())


def test_pause_waits_for_in_flight_run_and_wins_final_state():
    async def run():
        discord = BlockingDiscord()
        ctx = Context(discord=discord)
        seed(
            ctx,
            creatives=[creative("creative-a", advertiser_id="10")],
            campaigns=[
                campaign(
                    "campaign-a",
                    advertiser_id="10",
                    creative_id="creative-a",
                )
            ],
        )
        skill = AwinAffiliateSkill()

        run_task = asyncio.create_task(
            skill._manage_campaign_run_now(ctx, {"campaignId": "campaign-a"})
        )
        await asyncio.wait_for(discord.started.wait(), timeout=1)
        pause_task = asyncio.create_task(
            skill._manage_campaign_set_active(
                ctx,
                {"campaignId": "campaign-a", "active": False},
            )
        )
        await asyncio.sleep(0)
        assert not pause_task.done()

        discord.release.set()
        await asyncio.gather(run_task, pause_task)

        stored = stored_campaigns(ctx)["campaign-a"]
        assert stored.enabled is False
        assert stored.last_creative_id == "creative-a"
        assert "campaign:campaign-a" not in ctx.scheduler.jobs
        assert ctx.storage.values[CAMPAIGN_HISTORY_KEY][-1]["outcome"] == "sent"

    asyncio.run(run())


def test_delete_waits_for_in_flight_run_without_resurrecting_campaign():
    async def run():
        discord = BlockingDiscord()
        ctx = Context(discord=discord)
        seed(
            ctx,
            creatives=[creative("creative-a", advertiser_id="10")],
            campaigns=[
                campaign(
                    "campaign-a",
                    advertiser_id="10",
                    creative_id="creative-a",
                )
            ],
        )
        skill = AwinAffiliateSkill()

        run_task = asyncio.create_task(
            skill._manage_campaign_run_now(ctx, {"campaignId": "campaign-a"})
        )
        await asyncio.wait_for(discord.started.wait(), timeout=1)
        delete_task = asyncio.create_task(
            skill._manage_campaign_delete(ctx, {"campaignId": "campaign-a"})
        )
        await asyncio.sleep(0)
        assert not delete_task.done()

        discord.release.set()
        await asyncio.gather(run_task, delete_task)

        assert stored_campaigns(ctx) == {}
        assert "campaign:campaign-a" not in ctx.scheduler.jobs
        assert ctx.storage.values[CAMPAIGN_HISTORY_KEY][-1]["outcome"] == "sent"

    asyncio.run(run())


def test_update_waits_for_in_flight_run_and_preserves_rotation_progress():
    async def run():
        discord = BlockingDiscord()
        ctx = Context(discord=discord)
        seed(
            ctx,
            creatives=[creative("creative-a", advertiser_id="10")],
            campaigns=[
                campaign(
                    "campaign-a",
                    advertiser_id="10",
                    creative_id="creative-a",
                    name="Original",
                )
            ],
        )
        skill = AwinAffiliateSkill()

        run_task = asyncio.create_task(
            skill._manage_campaign_run_now(ctx, {"campaignId": "campaign-a"})
        )
        await asyncio.wait_for(discord.started.wait(), timeout=1)
        update_task = asyncio.create_task(
            skill._manage_campaign_update(
                ctx,
                {
                    "campaignId": "campaign-a",
                    "name": "Updated",
                    "intervalSeconds": 1800,
                },
            )
        )
        await asyncio.sleep(0)
        assert not update_task.done()

        discord.release.set()
        await asyncio.gather(run_task, update_task)

        stored = stored_campaigns(ctx)["campaign-a"]
        assert stored.name == "Updated"
        assert stored.interval_seconds == 1800
        assert stored.last_creative_id == "creative-a"
        assert ctx.scheduler.jobs["campaign:campaign-a"]["schedule"] == {
            "type": "interval",
            "seconds": 1800,
        }

    asyncio.run(run())


def test_scheduler_failure_rolls_back_created_campaign():
    async def run():
        ctx = Context(discord=TwoSendBarrierDiscord())
        ctx.scheduler.fail_upsert = True
        seed(
            ctx,
            creatives=[creative("creative-a", advertiser_id="10")],
            campaigns=[],
        )
        skill = AwinAffiliateSkill()

        with pytest.raises(RuntimeError, match="scheduler upsert"):
            await skill._manage_campaign_create(
                ctx,
                {
                    "name": "Campaign",
                    "advertiserId": "10",
                    "channelId": 50,
                    "selectedCreativeIds": ["creative-a"],
                    "rotation": "fixed",
                    "intervalSeconds": 900,
                },
            )

        assert stored_campaigns(ctx) == {}

    asyncio.run(run())
