from dataclasses import replace

from gamerhq_skill_awin_affiliate.creative_sources import (
    CreativeSnapshot,
    CreativeSourceAuthority,
)
from gamerhq_skill_awin_affiliate.models import Creative, CreativeState
from gamerhq_skill_awin_affiliate.sync import apply_creative_snapshot


def creative(
    creative_id: str,
    *,
    source: str = "authoritative-fixture",
    title: str | None = None,
    state: CreativeState = CreativeState.ACTIVE,
) -> Creative:
    return Creative(
        id=f"awin:3095707:129591:{creative_id}",
        provider="awin",
        publisher_id="3095707",
        advertiser_id="129591",
        external_creative_id=creative_id,
        creative_group_id=None,
        advertiser_name="Ugovaper",
        type="image",
        title=title,
        image_url=f"https://www.awin1.com/cshow.php?s={creative_id}&v=129591&r=3095707",
        tracking_url=f"https://www.awin1.com/cread.php?s={creative_id}&v=129591&r=3095707",
        source=source,
        state=state,
    )


def snapshot(*items: Creative) -> CreativeSnapshot:
    return CreativeSnapshot(
        source_id="authoritative-fixture",
        authority=CreativeSourceAuthority.AUTHORITATIVE,
        publisher_id="3095707",
        advertiser_id="129591",
        creatives=tuple(items),
    )


def test_authoritative_sync_tracks_new_active_missing_and_restored():
    records, first = apply_creative_snapshot([], snapshot(creative("1"), creative("2")), now=100)

    assert first.new == 2
    assert {item.state for item in records} == {CreativeState.NEW}

    records, second = apply_creative_snapshot(records, snapshot(creative("1"), creative("2")), now=200)

    assert second.unchanged == 2
    assert second.missing == 0
    assert {item.state for item in records} == {CreativeState.ACTIVE}

    records, third = apply_creative_snapshot(records, snapshot(creative("1")), now=300)
    by_id = {item.external_creative_id: item for item in records}

    assert third.missing == 1
    assert by_id["1"].state == CreativeState.ACTIVE
    assert by_id["2"].state == CreativeState.MISSING
    assert by_id["2"].last_seen_at == 200
    assert by_id["2"].last_synced_at == 300

    records, fourth = apply_creative_snapshot(records, snapshot(creative("1"), creative("2")), now=400)
    by_id = {item.external_creative_id: item for item in records}

    assert fourth.restored == 1
    assert by_id["2"].state == CreativeState.ACTIVE
    assert by_id["2"].first_seen_at == 100
    assert by_id["2"].last_seen_at == 400


def test_authoritative_sync_detects_payload_updates():
    records, _ = apply_creative_snapshot([], snapshot(creative("1", title="Old")), now=100)
    records, result = apply_creative_snapshot(records, snapshot(creative("1", title="New")), now=200)

    assert result.updated == 1
    assert records[0].title == "New"
    assert records[0].state == CreativeState.ACTIVE


def test_authoritative_sync_only_marks_records_owned_by_that_source_missing():
    manual = creative("99", source="manual_html", state=CreativeState.ACTIVE)
    authoritative = creative("1")

    records, _ = apply_creative_snapshot(
        [manual, authoritative],
        snapshot(),
        now=300,
    )
    by_id = {item.external_creative_id: item for item in records}

    assert by_id["1"].state == CreativeState.MISSING
    assert by_id["99"].state == CreativeState.ACTIVE


def test_upsert_only_snapshot_never_marks_missing():
    existing = creative("1", source="manual_html", state=CreativeState.ACTIVE)
    upsert = CreativeSnapshot(
        source_id="manual_html",
        authority=CreativeSourceAuthority.UPSERT_ONLY,
        publisher_id="3095707",
        advertiser_id="129591",
        creatives=(),
    )

    records, result = apply_creative_snapshot([existing], upsert, now=500)

    assert result.missing == 0
    assert records[0].state == CreativeState.ACTIVE


def test_snapshot_rejects_cross_advertiser_content():
    other = replace(creative("1"), advertiser_id="999")
    try:
        CreativeSnapshot(
            source_id="fixture",
            authority=CreativeSourceAuthority.AUTHORITATIVE,
            publisher_id="3095707",
            advertiser_id="129591",
            creatives=(other,),
        )
    except ValueError as exc:
        assert "different advertiser ID" in str(exc)
    else:
        raise AssertionError("Expected cross-advertiser snapshot to fail.")
