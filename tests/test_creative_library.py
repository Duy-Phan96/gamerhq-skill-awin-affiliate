import pytest

from gamerhq_skill_awin_affiliate.creative_library import list_page, preview_view, set_enabled
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState


def creative(
    id,
    *,
    advertiser_id="10",
    advertiser_name="Advertiser",
    enabled=True,
    state=CreativeState.ACTIVE,
    width=300,
    height=250,
):
    return Creative(
        id=id,
        provider="awin",
        publisher_id="20",
        advertiser_id=advertiser_id,
        external_creative_id=id,
        creative_group_id=None,
        advertiser_name=advertiser_name,
        type="image",
        image_url=f"https://www.awin1.com/cshow.php?s={id}",
        tracking_url=f"https://www.awin1.com/cread.php?s={id}",
        width=width,
        height=height,
        state=state,
        user_enabled=enabled,
    )


def test_list_page_filters_and_paginates():
    values = [
        creative("1"),
        creative("2", enabled=False),
        creative("3", advertiser_id="11"),
        creative("4", state=CreativeState.MISSING),
    ]

    page = list_page(
        values,
        advertiser_id="10",
        enabled_only=True,
        active_only=True,
        offset=0,
        limit=1,
    )

    assert page["total"] == 1
    assert [item["id"] for item in page["items"]] == ["1"]
    assert page["hasPrevious"] is False
    assert page["hasNext"] is False


def test_list_page_enforces_discord_friendly_page_size():
    with pytest.raises(ValueError, match="between 1 and 25"):
        list_page([creative("1")], limit=26)


def test_preview_is_discord_native_and_contains_disclosure():
    preview = preview_view(creative("1"))
    assert preview["discordPreview"]["button"]["label"] == "View offer"
    assert preview["discordPreview"]["disclosure"] == "Werbung · Affiliate-Link"
    assert preview["creative"]["dimensions"] == "300×250"


def test_bulk_enable_disable_preserves_order_and_rejects_unknown_ids():
    values = [creative("1"), creative("2")]
    changed, count = set_enabled(values, creative_ids=["1", "2"], enabled=False)
    assert count == 2
    assert [item.user_enabled for item in changed] == [False, False]

    with pytest.raises(KeyError, match="Unknown creativeId"):
        set_enabled(values, creative_ids=["missing"], enabled=False)
