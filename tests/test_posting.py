import pytest

from gamerhq_skill_awin_affiliate.models import Creative, CreativeState
from gamerhq_skill_awin_affiliate.posting import (
    read_last_creative_id,
    render_post,
    select_creative,
    with_last_creative,
)


def creative(id, *, enabled=True, state=CreativeState.ACTIVE, advertiser_id="10"):
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


def test_specific_rejects_disabled_or_missing_creative():
    with pytest.raises(ValueError, match="unavailable"):
        select_creative([creative("1", enabled=False)], mode="specific", creative_id="1")
    with pytest.raises(ValueError, match="unavailable"):
        select_creative([creative("1", state=CreativeState.MISSING)], mode="specific", creative_id="1")


def test_next_rotates_after_last_eligible_creative():
    values = [creative("a"), creative("b"), creative("c")]
    selected = select_creative(values, mode="next", advertiser_id="10", last_creative_id="b")
    assert selected.creative.id == "c"
    wrapped = select_creative(values, mode="next", advertiser_id="10", last_creative_id="c")
    assert wrapped.creative.id == "a"


def test_render_post_always_contains_disclosure_and_https_link_button():
    rendered = render_post(creative("1"), title="Deal", text="Limited offer")
    assert "Werbung · Affiliate-Link" in rendered["content"]
    assert rendered["embed"]["title"] == "Deal"
    assert rendered["embed"]["description"] == "Limited offer"
    assert rendered["linkButtons"][0]["url"].startswith("https://")


def test_post_state_round_trip_is_advertiser_scoped():
    state = with_last_creative({}, advertiser_id="10", creative_id="one")
    state = with_last_creative(state, advertiser_id="11", creative_id="two")
    assert read_last_creative_id(state, advertiser_id="10") == "one"
    assert read_last_creative_id(state, advertiser_id="11") == "two"
