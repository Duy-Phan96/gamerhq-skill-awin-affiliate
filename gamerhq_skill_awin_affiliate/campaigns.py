from __future__ import annotations

from dataclasses import dataclass, replace
import secrets
from typing import Any, Iterable, Mapping

from .models import Creative, CreativeState

CAMPAIGNS_KEY = "campaigns.v1"
CAMPAIGN_HANDLER_ID = "awin-affiliate.campaign.execute.v1"
MIN_INTERVAL_SECONDS = 15 * 60
MAX_CAMPAIGNS = 50
ROTATION_MODES = frozenset({"fixed", "sequential", "random", "shuffle"})
_ELIGIBLE_STATES = {CreativeState.ACTIVE, CreativeState.NEW}


@dataclass(frozen=True, slots=True)
class Campaign:
    id: str
    name: str
    advertiser_id: str
    channel_id: int
    selected_creative_ids: tuple[str, ...]
    rotation: str
    interval_seconds: int
    enabled: bool = True
    avoid_immediate_repeat: bool = True
    last_creative_id: str | None = None
    sequential_index: int = 0
    shuffle_remaining: tuple[str, ...] = ()
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "advertiserId": self.advertiser_id,
            "channelId": self.channel_id,
            "selectedCreativeIds": list(self.selected_creative_ids),
            "rotation": self.rotation,
            "intervalSeconds": self.interval_seconds,
            "enabled": self.enabled,
            "avoidImmediateRepeat": self.avoid_immediate_repeat,
            "lastCreativeId": self.last_creative_id,
            "sequentialIndex": self.sequential_index,
            "shuffleRemaining": list(self.shuffle_remaining),
            "blockedReason": self.blocked_reason,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Campaign":
        try:
            selected = value.get("selectedCreativeIds", ())
            shuffle = value.get("shuffleRemaining", ())
            if not isinstance(selected, (list, tuple)) or not isinstance(shuffle, (list, tuple)):
                raise TypeError
            campaign = cls(
                id=str(value["id"]),
                name=str(value["name"]),
                advertiser_id=str(value["advertiserId"]),
                channel_id=int(value["channelId"]),
                selected_creative_ids=tuple(str(item) for item in selected),
                rotation=str(value["rotation"]),
                interval_seconds=int(value["intervalSeconds"]),
                enabled=bool(value.get("enabled", True)),
                avoid_immediate_repeat=bool(value.get("avoidImmediateRepeat", True)),
                last_creative_id=str(value["lastCreativeId"]) if value.get("lastCreativeId") else None,
                sequential_index=int(value.get("sequentialIndex", 0)),
                shuffle_remaining=tuple(str(item) for item in shuffle),
                blocked_reason=str(value["blockedReason"]) if value.get("blockedReason") else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Stored Awin campaign is invalid.") from exc
        validate_campaign(campaign)
        return campaign


def validate_campaign(campaign: Campaign) -> None:
    if not campaign.id or len(campaign.id) > 64:
        raise ValueError("Campaign id is invalid.")
    if not campaign.name.strip() or len(campaign.name) > 80:
        raise ValueError("Campaign name must be 1-80 characters.")
    if not campaign.advertiser_id:
        raise ValueError("Campaign advertiser is required.")
    if campaign.channel_id <= 0:
        raise ValueError("Campaign channel must be positive.")
    if campaign.rotation not in ROTATION_MODES:
        raise ValueError("Campaign rotation must be fixed, sequential, random or shuffle.")
    if campaign.interval_seconds < MIN_INTERVAL_SECONDS:
        raise ValueError("Campaign interval must be at least 15 minutes.")
    if not campaign.selected_creative_ids:
        raise ValueError("Campaign needs at least one selected Creative.")
    if campaign.rotation == "fixed" and len(campaign.selected_creative_ids) != 1:
        raise ValueError("Fixed rotation requires exactly one selected Creative.")


def eligible_for_campaign(campaign: Campaign, creatives: Iterable[Creative]) -> list[Creative]:
    selected = set(campaign.selected_creative_ids)
    return sorted(
        [
            item for item in creatives
            if item.id in selected
            and item.advertiser_id == campaign.advertiser_id
            and item.user_enabled
            and item.state in _ELIGIBLE_STATES
        ],
        key=lambda item: item.id,
    )


def choose_campaign_creative(
    campaign: Campaign,
    creatives: Iterable[Creative],
) -> tuple[Creative | None, Campaign]:
    eligible = eligible_for_campaign(campaign, creatives)
    if not eligible:
        return None, replace(campaign, blocked_reason="No enabled active Creative is available.")

    by_id = {item.id: item for item in eligible}
    ids = [item.id for item in eligible]

    if campaign.rotation == "fixed":
        selected_id = ids[0]
        return by_id[selected_id], replace(campaign, last_creative_id=selected_id, blocked_reason=None)

    if campaign.rotation == "sequential":
        index = campaign.sequential_index % len(ids)
        selected_id = ids[index]
        return by_id[selected_id], replace(
            campaign,
            sequential_index=(index + 1) % len(ids),
            last_creative_id=selected_id,
            blocked_reason=None,
        )

    if campaign.rotation == "random":
        candidates = ids
        if campaign.avoid_immediate_repeat and len(ids) > 1 and campaign.last_creative_id in ids:
            candidates = [item for item in ids if item != campaign.last_creative_id]
        selected_id = secrets.choice(candidates)
        return by_id[selected_id], replace(campaign, last_creative_id=selected_id, blocked_reason=None)

    remaining = [item for item in campaign.shuffle_remaining if item in by_id]
    if not remaining:
        remaining = list(ids)
        secrets.SystemRandom().shuffle(remaining)
        if (
            campaign.avoid_immediate_repeat
            and len(remaining) > 1
            and remaining[0] == campaign.last_creative_id
        ):
            remaining[0], remaining[1] = remaining[1], remaining[0]
    selected_id = remaining.pop(0)
    return by_id[selected_id], replace(
        campaign,
        shuffle_remaining=tuple(remaining),
        last_creative_id=selected_id,
        blocked_reason=None,
    )
