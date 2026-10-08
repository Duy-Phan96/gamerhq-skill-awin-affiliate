import asyncio

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY
from gamerhq_skill_awin_affiliate.creative_sources import CreativeSourceAuthority
from gamerhq_skill_awin_affiliate.imports import AwinSavedPageCreativeSource
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState


HTML = """
<html><body>
<a href="https://www.awin1.com/cread.php?s=101&v=10&q=1&r=20">
  <img src="https://www.awin1.com/cshow.php?s=101&v=10&q=1&r=20"
       alt="Spring Sale" title="Spring Banner" width="300" height="250">
</a>
<a href="https://www.awin1.com/cread.php?s=102&v=10&q=2&r=20">
  <img src="https://www.awin1.com/cshow.php?s=102&v=10&q=2&r=20">
</a>
<a href="https://www.awin1.com/cread.php?s=201&v=11&q=3&r=20">
  <img src="https://www.awin1.com/cshow.php?s=201&v=11&q=3&r=20">
</a>
</body></html>
"""


def test_saved_page_groups_multiple_advertisers_and_keeps_metadata():
    snapshots = AwinSavedPageCreativeSource().snapshots(HTML)

    assert len(snapshots) == 2
    assert {(item.publisher_id, item.advertiser_id) for item in snapshots} == {
        ("20", "10"),
        ("20", "11"),
    }
    assert {item.authority for item in snapshots} == {CreativeSourceAuthority.UPSERT_ONLY}

    advertiser_10 = next(item for item in snapshots if item.advertiser_id == "10")
    first = next(item for item in advertiser_10.creatives if item.external_creative_id == "101")
    assert first.source == "saved_my_creative_html"
    assert first.title == "Spring Banner"
    assert first.description == "Spring Sale"
    assert first.width == 300
    assert first.height == 250


def test_only_explicit_complete_advertiser_becomes_authoritative():
    snapshots = AwinSavedPageCreativeSource().snapshots(
        HTML,
        complete_advertiser_id="10",
    )

    authority = {item.advertiser_id: item.authority for item in snapshots}
    assert authority["10"] == CreativeSourceAuthority.AUTHORITATIVE
    assert authority["11"] == CreativeSourceAuthority.UPSERT_ONLY


def test_unknown_complete_advertiser_is_rejected():
    try:
        AwinSavedPageCreativeSource().snapshots(HTML, complete_advertiser_id="999")
    except ValueError as exc:
        assert "was not found" in str(exc)
    else:
        raise AssertionError("Expected unknown complete advertiser to fail")


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


def existing(creative_id, advertiser_id):
    return Creative(
        id=f"awin:20:{advertiser_id}:{creative_id}",
        provider="awin",
        publisher_id="20",
        advertiser_id=advertiser_id,
        external_creative_id=creative_id,
        creative_group_id=None,
        advertiser_name=None,
        type="image",
        image_url=f"https://www.awin1.com/cshow.php?s={creative_id}&v={advertiser_id}&r=20",
        tracking_url=f"https://www.awin1.com/cread.php?s={creative_id}&v={advertiser_id}&r=20",
        source="saved_my_creative_html",
        state=CreativeState.ACTIVE,
        user_enabled=True,
        first_seen_at=1,
        last_seen_at=1,
        last_synced_at=1,
    )


def test_management_import_marks_missing_only_for_confirmed_complete_advertiser():
    async def run():
        ctx = Context()
        ctx.storage.values[STORAGE_KEY] = [
            existing("100", "10").to_dict(),
            existing("200", "11").to_dict(),
        ]
        skill = AwinAffiliateSkill()

        result = await skill._manage_import_saved_html(
            ctx,
            {
                "html": HTML,
                "completeAdvertiserId": "10",
            },
        )

        stored = {item.id: item for item in await skill.list_creatives(ctx)}
        assert stored["awin:20:10:100"].state == CreativeState.MISSING
        assert stored["awin:20:11:200"].state == CreativeState.ACTIVE
        assert result["import"]["missing"] == 1
        assert result["import"]["authoritativeAdvertiserId"] == "10"
        assert result["import"]["groups"] == 2
        assert len(result["import"]["groupResults"]) == 2

    asyncio.run(run())
