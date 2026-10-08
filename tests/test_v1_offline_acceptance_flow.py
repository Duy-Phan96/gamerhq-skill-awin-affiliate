import asyncio
import json
from types import SimpleNamespace

from skill_runtime import ExternalHttpResponse

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill
from gamerhq_skill_awin_affiliate.campaigns import CAMPAIGNS_KEY
from gamerhq_skill_awin_affiliate.posting import POST_STATE_KEY
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
    def __init__(self):
        self.calls = []

    async def write(self, **kwargs):
        self.calls.append(kwargs)


class Http:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    async def request(self, **kwargs):
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("Unexpected external HTTP request.")
        return self.responses.pop(0)


class Scheduler:
    def __init__(self):
        self.jobs = {}

    async def upsert_job(self, **kwargs):
        self.jobs[kwargs["key"]] = kwargs

    async def remove_job(self, *, key):
        self.jobs.pop(key, None)


class Discord:
    def __init__(self):
        self.sent = []

    async def get_channel(self, *, channel_id):
        return SimpleNamespace(id=channel_id, name="awin-test", kind="text")

    async def send_message(self, **kwargs):
        self.sent.append(kwargs)
        return 9000 + len(self.sent)


class Context:
    def __init__(self, *responses):
        self.guild_id = 123
        self.storage = Storage()
        self.secrets = Secrets()
        self.audit = Audit()
        self.http = Http(*responses)
        self.scheduler = Scheduler()
        self.discord = Discord()


def response(payload, status=200):
    return ExternalHttpResponse(
        status=status,
        headers={"content-type": "application/json"},
        body=json.dumps(payload),
    )


HTML = """
<!-- START ADVERTISER: Test Advertiser from awin.com -->
<a rel="sponsored"
   href="https://www.awin1.com/cread.php?s=101&v=129591&q=615955&r=3095707">
  <img
    src="https://www.awin1.com/cshow.php?s=101&v=129591&q=615955&r=3095707"
    alt="Test Banner"
    width="300"
    height="250">
</a>
<!-- END ADVERTISER: Test Advertiser from awin.com -->
"""


def test_complete_v1_management_flow_survives_skill_reinstantiation():
    async def run():
        ctx = Context(
            response(
                [
                    {
                        "accountId": 3095707,
                        "accountName": "Test Publisher",
                        "accountType": "publisher",
                        "userRole": "admin",
                    }
                ]
            ),
            response(
                [
                    {
                        "id": 129591,
                        "name": "Test Advertiser",
                        "status": "active",
                        "relationship": "joined",
                        "currencyCode": "EUR",
                        "primaryRegion": {"countryCode": "DE"},
                    }
                ]
            ),
        )
        skill = AwinAffiliateSkill()

        # 1. Connect and auto-select the only publisher account.
        connected = await skill._manage_setup_connect(
            ctx,
            {"accessToken": "test-token"},
        )
        assert connected["setup"]["connected"] is True
        assert connected["setup"]["selectionRequired"] is False
        assert connected["setup"]["publisher"] == {
            "id": "3095707",
            "name": "Test Publisher",
        }
        assert ctx.secrets.values[ACCESS_TOKEN_SECRET] == "test-token"
        assert ctx.storage.values[SETTINGS_KEY]["publisherId"] == "3095707"
        assert "test-token" not in repr(connected)

        # 2. Discover joined advertisers through the public management contract.
        advertisers = await skill._manage_advertisers_list(
            ctx,
            {"relationship": "joined"},
        )
        assert advertisers["advertisers"][0]["id"] == "129591"
        assert advertisers["advertisers"][0]["name"] == "Test Advertiser"

        # 3. Import a saved My Creative page. No complete advertiser is supplied,
        # so the import stays UPSERT_ONLY.
        imported = await skill._manage_import_saved_html(
            ctx,
            {"html": HTML},
        )
        assert imported["import"]["groups"] == 1
        assert imported["import"]["new"] == 1
        assert imported["import"]["missing"] == 0
        assert imported["import"]["authoritativeAdvertiserId"] is None

        library = await skill._manage_list_creatives(
            ctx,
            {
                "advertiserId": "129591",
                "enabledOnly": True,
                "activeOnly": True,
                "offset": 0,
                "limit": 25,
            },
        )
        items = library["creatives"]["items"]
        assert len(items) == 1
        creative_id = items[0]["id"]
        assert items[0]["dimensions"] == "300×250"

        # 4. Preview does not send. Confirmation uses the exact previewed Creative.
        preview = await skill._manage_post_preview(
            ctx,
            {
                "channelId": 50,
                "selectionMode": "specific",
                "creativeId": creative_id,
                "title": "Acceptance deal",
            },
        )
        assert ctx.discord.sent == []
        assert preview["confirmPayload"]["creativeId"] == creative_id
        assert "Werbung · Affiliate-Link" in preview["preview"]["content"]

        sent = await skill._manage_post_send(ctx, preview["confirmPayload"])
        assert sent["sent"] is True
        assert sent["creativeId"] == creative_id
        assert len(ctx.discord.sent) == 1
        assert ctx.storage.values[POST_STATE_KEY]["advertisers"]["129591"]["lastCreativeId"] == creative_id

        # 5. Create and exercise a standalone campaign.
        created = await skill._manage_campaign_create(
            ctx,
            {
                "name": "Acceptance Campaign",
                "advertiserId": "129591",
                "channelId": 50,
                "selectedCreativeIds": [creative_id],
                "rotation": "fixed",
                "intervalSeconds": 900,
                "enabled": True,
                "avoidImmediateRepeat": True,
            },
        )
        campaign_id = created["campaign"]["id"]
        assert created["campaign"]["status"] == "active"
        assert f"campaign:{campaign_id}" in ctx.scheduler.jobs

        stored_before_preview = list(ctx.storage.values[CAMPAIGNS_KEY])
        next_preview = await skill._manage_campaign_preview_next(
            ctx,
            {"campaignId": campaign_id},
        )
        assert next_preview["blocked"] is False
        assert next_preview["preview"]["creativeId"] == creative_id
        assert next_preview["rotationMutationApplied"] is False
        assert ctx.storage.values[CAMPAIGNS_KEY] == stored_before_preview

        run_now = await skill._manage_campaign_run_now(
            ctx,
            {"campaignId": campaign_id},
        )
        assert run_now["sent"] is True
        assert len(ctx.discord.sent) == 2

        history = await skill._manage_campaign_history(
            ctx,
            {"campaignId": campaign_id, "limit": 25},
        )
        assert history["history"][0]["outcome"] == "sent"
        assert history["history"][0]["creativeId"] == creative_id

        # 6. Simulate process-level Skill reinstantiation while retaining the
        # host-provided persistent ports/state.
        restarted_skill = AwinAffiliateSkill()

        setup_after_restart = await restarted_skill._manage_setup_status(ctx, {})
        campaign_after_restart = await restarted_skill._manage_campaign_get(
            ctx,
            {"campaignId": campaign_id},
        )
        creatives_after_restart = await restarted_skill._manage_list_creatives(
            ctx,
            {"offset": 0, "limit": 25},
        )

        assert setup_after_restart["setup"]["connected"] is True
        assert setup_after_restart["setup"]["publisher"]["id"] == "3095707"
        assert campaign_after_restart["campaign"]["status"] == "active"
        assert campaign_after_restart["campaign"]["eligibleCreativeCount"] == 1
        assert creatives_after_restart["creatives"]["total"] == 1

        # 7. Diagnostics are aggregate-only and must not leak the token.
        diagnostics = await restarted_skill._manage_diagnostics(ctx, {})
        serialized = repr(diagnostics)
        assert diagnostics["diagnostics"]["setup"]["connected"] is True
        assert diagnostics["diagnostics"]["creatives"]["total"] == 1
        assert diagnostics["diagnostics"]["campaigns"]["active"] == 1
        assert diagnostics["diagnostics"]["deliveryHistory"]["sent"] == 1
        assert "test-token" not in serialized
        assert "••••••••" not in serialized

        # Only the expected account/programme provider requests were made.
        assert len(ctx.http.calls) == 2
        assert ctx.http.responses == []

    asyncio.run(run())
