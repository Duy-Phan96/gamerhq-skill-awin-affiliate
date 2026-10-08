from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Mapping


class CreativeState(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MISSING = "MISSING"
    NEW = "NEW"


@dataclass(frozen=True, slots=True)
class Creative:
    id: str
    provider: str
    publisher_id: str
    advertiser_id: str
    external_creative_id: str
    creative_group_id: str | None
    advertiser_name: str | None
    type: str
    image_url: str
    tracking_url: str
    title: str | None = None
    description: str | None = None
    width: int | None = None
    height: int | None = None
    locale: str | None = None
    tags: tuple[str, ...] = ()
    source: str = "manual_html"
    state: CreativeState = CreativeState.ACTIVE
    user_enabled: bool = True
    first_seen_at: int | None = None
    last_seen_at: int | None = None
    last_synced_at: int | None = None
    metadata: Mapping[str, Any] | None = None

    def with_seen_at(self, timestamp: int) -> "Creative":
        return replace(
            self,
            first_seen_at=self.first_seen_at if self.first_seen_at is not None else timestamp,
            last_seen_at=timestamp,
            last_synced_at=timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "publisherId": self.publisher_id,
            "advertiserId": self.advertiser_id,
            "externalCreativeId": self.external_creative_id,
            "creativeGroupId": self.creative_group_id,
            "advertiserName": self.advertiser_name,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "imageUrl": self.image_url,
            "trackingUrl": self.tracking_url,
            "width": self.width,
            "height": self.height,
            "locale": self.locale,
            "tags": list(self.tags),
            "source": self.source,
            "state": self.state.value,
            "userEnabled": self.user_enabled,
            "firstSeenAt": self.first_seen_at,
            "lastSeenAt": self.last_seen_at,
            "lastSyncedAt": self.last_synced_at,
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Creative":
        try:
            state = CreativeState(str(value.get("state", CreativeState.ACTIVE.value)))
            tags_raw = value.get("tags", ())
            if not isinstance(tags_raw, (list, tuple)):
                raise TypeError
            user_enabled = value.get("userEnabled", True)
            if not isinstance(user_enabled, bool):
                raise TypeError
            return cls(
                id=str(value["id"]),
                provider=str(value["provider"]),
                publisher_id=str(value["publisherId"]),
                advertiser_id=str(value["advertiserId"]),
                external_creative_id=str(value["externalCreativeId"]),
                creative_group_id=_optional_str(value.get("creativeGroupId")),
                advertiser_name=_optional_str(value.get("advertiserName")),
                type=str(value["type"]),
                title=_optional_str(value.get("title")),
                description=_optional_str(value.get("description")),
                image_url=str(value["imageUrl"]),
                tracking_url=str(value["trackingUrl"]),
                width=_optional_int(value.get("width")),
                height=_optional_int(value.get("height")),
                locale=_optional_str(value.get("locale")),
                tags=tuple(str(item) for item in tags_raw),
                source=str(value.get("source", "manual_html")),
                state=state,
                user_enabled=user_enabled,
                first_seen_at=_optional_int(value.get("firstSeenAt")),
                last_seen_at=_optional_int(value.get("lastSeenAt")),
                last_synced_at=_optional_int(value.get("lastSyncedAt")),
                metadata=dict(value.get("metadata") or {}),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Stored Awin creative is invalid.") from exc


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean is not a valid integer.")
    return int(value)
