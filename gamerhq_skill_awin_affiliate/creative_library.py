from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from .models import Creative, CreativeState

MAX_PAGE_SIZE = 25
MAX_BULK_IDS = 100


def _matches(
    creative: Creative,
    *,
    advertiser_id: str | None = None,
    enabled_only: bool = False,
    active_only: bool = False,
    creative_type: str | None = None,
) -> bool:
    if advertiser_id is not None and creative.advertiser_id != advertiser_id:
        return False
    if enabled_only and not creative.user_enabled:
        return False
    if active_only and creative.state not in {CreativeState.ACTIVE, CreativeState.NEW}:
        return False
    if creative_type is not None and creative.type != creative_type:
        return False
    return True


def list_page(
    creatives: Iterable[Creative],
    *,
    advertiser_id: str | None = None,
    enabled_only: bool = False,
    active_only: bool = False,
    creative_type: str | None = None,
    offset: int = 0,
    limit: int = MAX_PAGE_SIZE,
) -> dict[str, Any]:
    if offset < 0:
        raise ValueError("offset must be non-negative.")
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError(f"limit must be between 1 and {MAX_PAGE_SIZE}.")

    filtered = [
        creative
        for creative in creatives
        if _matches(
            creative,
            advertiser_id=advertiser_id,
            enabled_only=enabled_only,
            active_only=active_only,
            creative_type=creative_type,
        )
    ]
    filtered.sort(
        key=lambda creative: (
            creative.advertiser_name or "",
            creative.width or 0,
            creative.height or 0,
            creative.id,
        )
    )
    page = filtered[offset : offset + limit]
    return {
        "items": [management_view(creative) for creative in page],
        "total": len(filtered),
        "offset": offset,
        "limit": limit,
        "hasPrevious": offset > 0,
        "hasNext": offset + len(page) < len(filtered),
    }


def management_view(creative: Creative) -> dict[str, Any]:
    dimensions = None
    if creative.width is not None and creative.height is not None:
        dimensions = f"{creative.width}×{creative.height}"
    return {
        "id": creative.id,
        "advertiserId": creative.advertiser_id,
        "advertiserName": creative.advertiser_name,
        "type": creative.type,
        "title": creative.title,
        "dimensions": dimensions,
        "imageUrl": creative.image_url,
        "trackingUrl": creative.tracking_url,
        "state": creative.state.value,
        "userEnabled": creative.user_enabled,
        "source": creative.source,
        "lastSeenAt": creative.last_seen_at,
        "lastSyncedAt": creative.last_synced_at,
    }


def preview_view(
    creative: Creative,
    *,
    disclosure: str = "Werbung · Affiliate-Link",
    supporting_text: str = "Mit Nutzung des Links unterstützt ihr den Server.",
) -> dict[str, Any]:
    return {
        "creative": management_view(creative),
        "discordPreview": {
            "title": creative.advertiser_name or creative.title or "Awin offer",
            "imageUrl": creative.image_url,
            "button": {
                "label": "View offer",
                "url": creative.tracking_url,
            },
            "disclosure": disclosure,
            "supportingText": supporting_text,
        },
    }


def set_enabled(creatives: Iterable[Creative], *, creative_ids: Iterable[str], enabled: bool) -> tuple[list[Creative], int]:
    ids = tuple(dict.fromkeys(str(value).strip() for value in creative_ids if str(value).strip()))
    if not ids:
        raise ValueError("At least one creativeId is required.")
    if len(ids) > MAX_BULK_IDS:
        raise ValueError(f"At most {MAX_BULK_IDS} creative IDs can be changed at once.")

    wanted = set(ids)
    found: set[str] = set()
    result: list[Creative] = []
    changed = 0
    for creative in creatives:
        if creative.id in wanted:
            found.add(creative.id)
            if creative.user_enabled != enabled:
                creative = replace(creative, user_enabled=enabled)
                changed += 1
        result.append(creative)

    missing = sorted(wanted - found)
    if missing:
        raise KeyError("Unknown creativeId: " + ", ".join(missing))
    return result, changed
