from gamerhq_skill_awin_affiliate.campaigns import Campaign
from gamerhq_skill_awin_affiliate.diagnostics import build_diagnostics
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState


def creative(id, *, state=CreativeState.ACTIVE, enabled=True):
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


def campaign(id, *, enabled=True, blocked_reason=None):
    return Campaign(
        id=id,
        name=id,
        advertiser_id="10",
        channel_id=50,
        selected_creative_ids=("a",),
        rotation="fixed",
        interval_seconds=10800,
        enabled=enabled,
        blocked_reason=blocked_reason,
    )


def test_diagnostics_aggregates_without_returning_token_material():
    result = build_diagnostics(
        setup_status={
            "connected": True,
            "publisherSelected": True,
            "publisher": {"id": "20", "name": "GamerHQ"},
            "token": "••••••••",
        },
        creatives=[
            creative("a"),
            creative("b", enabled=False),
            creative("c", state=CreativeState.MISSING),
        ],
        campaigns=[
            campaign("active"),
            campaign("paused", enabled=False),
            campaign("blocked", blocked_reason="No enabled active Creative is available."),
        ],
        history=[
            {"campaignId": "active", "outcome": "sent"},
            {"campaignId": "active", "outcome": "failed", "reason": "discord-send-failed"},
            {"campaignId": "blocked", "outcome": "blocked"},
        ],
    )

    assert result["setup"]["tokenStored"] is True
    assert "token" not in result["setup"]
    assert result["creatives"]["total"] == 3
    assert result["creatives"]["disabled"] == 1
    assert result["creatives"]["byState"]["MISSING"] == 1
    assert result["campaigns"] == {"total": 3, "active": 1, "paused": 1, "blocked": 1}
    assert result["deliveryHistory"]["failed"] == 1
