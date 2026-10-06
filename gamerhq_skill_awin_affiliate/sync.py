from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from .creative_sources import CreativeSnapshot, CreativeSourceAuthority
from .models import Creative, CreativeState


@dataclass(frozen=True, slots=True)
class CreativeSyncResult:
    source_id: str
    publisher_id: str
    advertiser_id: str
    found: int
    new: int
    updated: int
    missing: int
    restored: int
    unchanged: int
    total: int

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source_id,
            "publisherId": self.publisher_id,
            "advertiserId": self.advertiser_id,
            "found": self.found,
            "new": self.new,
            "updated": self.updated,
            "missing": self.missing,
            "restored": self.restored,
            "unchanged": self.unchanged,
            "total": self.total,
        }


def _same_payload(left: Creative, right: Creative) -> bool:
    ignored = {
        "state",
        "user_enabled",
        "first_seen_at",
        "last_seen_at",
        "last_synced_at",
    }
    left_data = left.to_dict()
    right_data = right.to_dict()
    mapping = {
        "state": "state",
        "user_enabled": "userEnabled",
        "first_seen_at": "firstSeenAt",
        "last_seen_at": "lastSeenAt",
        "last_synced_at": "lastSyncedAt",
    }
    for field in ignored:
        key = mapping[field]
        left_data.pop(key, None)
        right_data.pop(key, None)
    return left_data == right_data


def apply_creative_snapshot(
    current: Iterable[Creative],
    snapshot: CreativeSnapshot,
    *,
    now: int,
) -> tuple[list[Creative], CreativeSyncResult]:
    if now < 0:
        raise ValueError("Sync timestamp must be non-negative.")

    records = {creative.id: creative for creative in current}
    incoming = {creative.id: creative for creative in snapshot.creatives}
    if len(incoming) != len(snapshot.creatives):
        raise ValueError("Creative snapshot contains duplicate stable IDs.")

    new_count = 0
    updated = 0
    restored = 0
    unchanged = 0

    for creative_id, candidate in incoming.items():
        existing = records.get(creative_id)
        if existing is None:
            records[creative_id] = replace(
                candidate,
                source=snapshot.source_id,
                state=CreativeState.NEW,
                first_seen_at=now,
                last_seen_at=now,
                last_synced_at=now,
            )
            new_count += 1
            continue

        was_missing = existing.state == CreativeState.MISSING
        normalized = replace(
            candidate,
            source=snapshot.source_id,
            state=CreativeState.ACTIVE,
            user_enabled=existing.user_enabled,
            first_seen_at=existing.first_seen_at if existing.first_seen_at is not None else now,
            last_seen_at=now,
            last_synced_at=now,
        )
        records[creative_id] = normalized
        if was_missing:
            restored += 1
        elif _same_payload(existing, normalized):
            unchanged += 1
        else:
            updated += 1

    missing = 0
    if snapshot.authority == CreativeSourceAuthority.AUTHORITATIVE:
        incoming_ids = set(incoming)
        for creative_id, existing in tuple(records.items()):
            if (
                creative_id not in incoming_ids
                and existing.provider == "awin"
                and existing.publisher_id == snapshot.publisher_id
                and existing.advertiser_id == snapshot.advertiser_id
                and existing.source == snapshot.source_id
                and existing.state != CreativeState.MISSING
            ):
                records[creative_id] = replace(
                    existing,
                    state=CreativeState.MISSING,
                    last_synced_at=now,
                )
                missing += 1

    ordered = sorted(records.values(), key=lambda item: item.id)
    return ordered, CreativeSyncResult(
        source_id=snapshot.source_id,
        publisher_id=snapshot.publisher_id,
        advertiser_id=snapshot.advertiser_id,
        found=len(snapshot.creatives),
        new=new_count,
        updated=updated,
        missing=missing,
        restored=restored,
        unchanged=unchanged,
        total=len(ordered),
    )
