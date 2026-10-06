import asyncio

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY
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


class Context:
    def __init__(self):
        self.guild_id = 123
        self.storage = Storage()
        self.audit = Audit()


def creative(id, *, advertiser_id="10", enabled=True, state=CreativeState.ACTIVE):
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
        width=300,
        height=250,
        state=state,
        user_enabled=enabled,
    )


def seed(ctx, *values):
    ctx.storage.values[STORAGE_KEY] = [value.to_dict() for value in values]


def test_management_list_get_preview_and_bulk_toggle():
    async def run():
        ctx = Context()
        seed(ctx, creative("1"), creative("2"), creative("3", advertiser_id="11"))
        skill = AwinAffiliateSkill()

        listed = await skill._manage_list_creatives(
            ctx,
            {"advertiserId": "10", "activeOnly": True, "limit": 25},
        )
        assert listed["creatives"]["total"] == 2
        assert [item["id"] for item in listed["creatives"]["items"]] == ["1", "2"]

        item = await skill._manage_get_creative(ctx, {"creativeId": "1"})
        assert item["creative"]["id"] == "1"

        preview = await skill._manage_preview_creative(ctx, {"creativeId": "1"})
        assert preview["discordPreview"]["button"]["url"].endswith("s=1")
        assert preview["discordPreview"]["disclosure"] == "Werbung · Affiliate-Link"

        changed = await skill._manage_set_creatives_enabled(
            ctx,
            {"creativeIds": ["1", "2"], "enabled": False},
        )
        assert changed == {"updated": 2, "changed": 2, "enabled": False}

        stored = await skill.list_creatives(ctx)
        assert [item.user_enabled for item in stored if item.advertiser_id == "10"] == [False, False]
        assert ctx.audit.calls[-1]["action"] == "creatives.enabled-changed"

    asyncio.run(run())


def test_advertiser_enable_all_can_target_only_active_creatives():
    async def run():
        ctx = Context()
        seed(
            ctx,
            creative("1", enabled=False),
            creative("2", enabled=False, state=CreativeState.MISSING),
            creative("3", advertiser_id="11", enabled=False),
        )
        skill = AwinAffiliateSkill()

        result = await skill._manage_set_advertiser_creatives_enabled(
            ctx,
            {"advertiserId": "10", "enabled": True, "activeOnly": True},
        )
        assert result == {"updated": 1, "changed": 1, "enabled": True}

        stored = {item.id: item for item in await skill.list_creatives(ctx)}
        assert stored["1"].user_enabled is True
        assert stored["2"].user_enabled is False
        assert stored["3"].user_enabled is False

    asyncio.run(run())


def test_bulk_toggle_rejects_unknown_creative_without_partial_write():
    async def run():
        ctx = Context()
        seed(ctx, creative("1"), creative("2"))
        before = list(ctx.storage.values[STORAGE_KEY])
        skill = AwinAffiliateSkill()

        try:
            await skill._manage_set_creatives_enabled(
                ctx,
                {"creativeIds": ["1", "missing"], "enabled": False},
            )
        except ValueError as exc:
            assert "Unknown creativeId" in str(exc)
        else:
            raise AssertionError("Expected unknown creative ID to fail")

        assert ctx.storage.values[STORAGE_KEY] == before

    asyncio.run(run())
