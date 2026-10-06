from __future__ import annotations

from dataclasses import dataclass
import secrets
from typing import Any, Iterable, Mapping

from .models import Creative, CreativeState

POST_STATE_KEY = "post-state.v1"
DEFAULT_DISCLOSURE = "Werbung · Affiliate-Link"
DEFAULT_SUPPORTING_TEXT = "Mit Nutzung des Links unterstützt ihr den Server."
_ALLOWED_STATES = {CreativeState.ACTIVE, CreativeState.NEW}
_ALLOWED_MODES = {"specific", "random", "next"}


@dataclass(frozen=True, slots=True)
class PostSelection:
    creative: Creative
    mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "creativeId": self.creative.id,
            "advertiserId": self.creative.advertiser_id,
            "mode": self.mode,
        }


def eligible_creatives(
    creatives: Iterable[Creative],
    *,
    advertiser_id: str | None = None,
) -> list[Creative]:
    result = [
        item
        for item in creatives
        if item.user_enabled
        and item.state in _ALLOWED_STATES
        and (advertiser_id is None or item.advertiser_id == advertiser_id)
    ]
    return sorted(result, key=lambda item: item.id)


def select_creative(
    creatives: Iterable[Creative],
    *,
    mode: str,
    creative_id: str | None = None,
    advertiser_id: str | None = None,
    last_creative_id: str | None = None,
) -> PostSelection:
    normalized_mode = str(mode).strip().lower()
    if normalized_mode not in _ALLOWED_MODES:
        raise ValueError("selectionMode must be specific, random or next.")

    eligible = eligible_creatives(creatives, advertiser_id=advertiser_id)
    if not eligible:
        raise ValueError("No enabled active Awin creative is available for this selection.")

    if normalized_mode == "specific":
        requested = str(creative_id or "").strip()
        if not requested:
            raise ValueError("creativeId is required for specific selection.")
        selected = next((item for item in eligible if item.id == requested), None)
        if selected is None:
            raise ValueError("Selected creative is unavailable, disabled or no longer active.")
        return PostSelection(selected, normalized_mode)

    if normalized_mode == "random":
        return PostSelection(secrets.choice(eligible), normalized_mode)

    if last_creative_id:
        for index, item in enumerate(eligible):
            if item.id == last_creative_id:
                return PostSelection(eligible[(index + 1) % len(eligible)], normalized_mode)
    return PostSelection(eligible[0], normalized_mode)


def render_post(
    creative: Creative,
    *,
    title: str | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    clean_title = str(title or "").strip()
    clean_text = str(text or "").strip()
    if len(clean_title) > 256:
        raise ValueError("Post title must be at most 256 characters.")
    if len(clean_text) > 2000:
        raise ValueError("Post text must be at most 2000 characters.")

    embed: dict[str, Any] = {
        "title": clean_title or creative.advertiser_name or creative.title or "Awin offer",
        "image": {"url": creative.image_url},
    }
    description = clean_text or creative.description
    if description:
        embed["description"] = str(description)[:4096]

    content = f"**{DEFAULT_DISCLOSURE}**\n{DEFAULT_SUPPORTING_TEXT}"
    return {
        "content": content,
        "embed": embed,
        "linkButtons": (
            {
                "label": "View offer",
                "url": creative.tracking_url,
            },
        ),
    }


def read_last_creative_id(state: Any, *, advertiser_id: str) -> str | None:
    if not isinstance(state, Mapping):
        return None
    advertisers = state.get("advertisers")
    if not isinstance(advertisers, Mapping):
        return None
    row = advertisers.get(str(advertiser_id))
    if not isinstance(row, Mapping):
        return None
    value = row.get("lastCreativeId")
    return str(value).strip() if value else None


def with_last_creative(state: Any, *, advertiser_id: str, creative_id: str) -> dict[str, Any]:
    advertisers: dict[str, Any] = {}
    if isinstance(state, Mapping) and isinstance(state.get("advertisers"), Mapping):
        advertisers = {
            str(key): dict(value) if isinstance(value, Mapping) else {}
            for key, value in state["advertisers"].items()
        }
    advertisers[str(advertiser_id)] = {"lastCreativeId": str(creative_id)}
    return {"schemaVersion": 1, "advertisers": advertisers}
