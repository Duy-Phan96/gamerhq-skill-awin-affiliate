from gamerhq_skill_awin_affiliate.campaigns import Campaign, choose_campaign_creative
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState


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


def campaign(rotation, ids=("a","b","c")):
    return Campaign(
        id="campaign-1",
        name="Deals",
        advertiser_id="10",
        channel_id=50,
        selected_creative_ids=tuple(ids),
        rotation=rotation,
        interval_seconds=10800,
    )


def test_fixed_requires_and_uses_one_creative():
    selected, updated = choose_campaign_creative(campaign("fixed", ("a",)), [creative("a")])
    assert selected.id == "a"
    assert updated.last_creative_id == "a"


def test_sequential_rotation_wraps():
    value = campaign("sequential", ("a","b"))
    first, value = choose_campaign_creative(value, [creative("a"), creative("b")])
    second, value = choose_campaign_creative(value, [creative("a"), creative("b")])
    third, value = choose_campaign_creative(value, [creative("a"), creative("b")])
    assert [first.id, second.id, third.id] == ["a", "b", "a"]


def test_random_avoids_immediate_repeat_when_possible():
    value = campaign("random")
    value = Campaign(**{**value.__dict__, "last_creative_id": "a"}) if hasattr(value, "__dict__") else value
    # dataclass uses slots, so reconstruct explicitly
    value = Campaign(
        id=value.id, name=value.name, advertiser_id=value.advertiser_id,
        channel_id=value.channel_id, selected_creative_ids=value.selected_creative_ids,
        rotation=value.rotation, interval_seconds=value.interval_seconds,
        last_creative_id="a",
    )
    selected, _ = choose_campaign_creative(value, [creative("a"), creative("b"), creative("c")])
    assert selected.id in {"b", "c"}


def test_shuffle_uses_all_before_new_cycle():
    value = campaign("shuffle")
    seen = []
    for _ in range(3):
        selected, value = choose_campaign_creative(value, [creative("a"), creative("b"), creative("c")])
        seen.append(selected.id)
    assert set(seen) == {"a", "b", "c"}


def test_zero_eligible_creatives_blocks_without_selection():
    selected, updated = choose_campaign_creative(
        campaign("sequential"),
        [creative("a", enabled=False), creative("b", state=CreativeState.MISSING)],
    )
    assert selected is None
    assert "No enabled active" in updated.blocked_reason
