import asyncio
from types import SimpleNamespace

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState
from gamerhq_skill_awin_affiliate.posting import POST_STATE_KEY, read_last_creative_id


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


class Discord:
    def __init__(self):
        self.sent = []

    async def get_channel(self, *, channel_id):
        return SimpleNamespace(id=channel_id, name="deals", kind="text")

    async def send_message(self, **kwargs):
        self.sent.append(kwargs)
        return 9001


class Context:
    def __init__(self):
        self.guild_id = 123
        self.storage = Storage()
        self.audit = Audit()
        self.discord = Discord()


def creative(id, *, enabled=True, state=CreativeState.ACTIVE):
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


def seed(ctx, *items):
    ctx.storage.values[STORAGE_KEY] = [item.to_dict() for item in items]


def test_preview_does_not_send_and_confirm_uses_same_creative():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b"))
        skill = AwinAffiliateSkill()

        preview = await skill._manage_post_preview(
            ctx,
            {
                "channelId": 50,
                "selectionMode": "specific",
                "creativeId": "a",
                "title": "Featured deal",
                "text": "Take a look",
            },
        )

        assert ctx.discord.sent == []
        assert preview["preview"]["selection"]["creativeId"] == "a"
        assert preview["confirmPayload"]["creativeId"] == "a"
        assert "Werbung · Affiliate-Link" in preview["preview"]["content"]

        result = await skill._manage_post_send(ctx, preview["confirmPayload"])

        assert result["messageId"] == 9001
        assert result["creativeId"] == "a"
        assert len(ctx.discord.sent) == 1
        sent = ctx.discord.sent[0]
        assert sent["embed"]["title"] == "Featured deal"
        assert sent["link_buttons"][0]["label"] == "View offer"
        assert sent["link_buttons"][0]["url"].endswith("s=a")
        assert "Werbung · Affiliate-Link" in sent["content"]

    asyncio.run(run())


def test_next_preview_uses_last_successful_post_per_advertiser():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"), creative("b"), creative("c"))
        ctx.storage.values[POST_STATE_KEY] = {
            "schemaVersion": 1,
            "advertisers": {"10": {"lastCreativeId": "b"}},
        }
        skill = AwinAffiliateSkill()

        preview = await skill._manage_post_preview(
            ctx,
            {"channelId": 50, "selectionMode": "next", "advertiserId": "10"},
        )
        assert preview["confirmPayload"]["creativeId"] == "c"

        await skill._manage_post_send(ctx, preview["confirmPayload"])
        state = ctx.storage.values[POST_STATE_KEY]
        assert read_last_creative_id(state, advertiser_id="10") == "c"

    asyncio.run(run())


def test_random_and_next_require_advertiser_scope():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"))
        skill = AwinAffiliateSkill()
        for mode in ("random", "next"):
            try:
                await skill._manage_post_preview(
                    ctx,
                    {"channelId": 50, "selectionMode": mode},
                )
            except ValueError as exc:
                assert "advertiserId is required" in str(exc)
            else:
                raise AssertionError("Expected advertiser-scoped selection to fail")

    asyncio.run(run())


def test_send_revalidates_creative_after_preview():
    async def run():
        ctx = Context()
        seed(ctx, creative("a"))
        skill = AwinAffiliateSkill()

        preview = await skill._manage_post_preview(
            ctx,
            {"channelId": 50, "selectionMode": "specific", "creativeId": "a"},
        )
        seed(ctx, creative("a", state=CreativeState.MISSING))

        try:
            await skill._manage_post_send(ctx, preview["confirmPayload"])
        except ValueError as exc:
            assert "unavailable" in str(exc)
        else:
            raise AssertionError("Expected stale preview to fail closed")

        assert ctx.discord.sent == []

    asyncio.run(run())
