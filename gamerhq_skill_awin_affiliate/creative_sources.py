from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .models import Creative


class CreativeSourceAuthority(StrEnum):
    UPSERT_ONLY = "UPSERT_ONLY"
    AUTHORITATIVE = "AUTHORITATIVE"


@dataclass(frozen=True, slots=True)
class CreativeSnapshot:
    source_id: str
    authority: CreativeSourceAuthority
    publisher_id: str
    advertiser_id: str
    creatives: tuple[Creative, ...]

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("Creative source ID is required.")
        if not self.publisher_id.strip():
            raise ValueError("Creative snapshot publisher ID is required.")
        if not self.advertiser_id.strip():
            raise ValueError("Creative snapshot advertiser ID is required.")
        for creative in self.creatives:
            if creative.publisher_id != self.publisher_id:
                raise ValueError("Creative snapshot contains a different publisher ID.")
            if creative.advertiser_id != self.advertiser_id:
                raise ValueError("Creative snapshot contains a different advertiser ID.")


class CreativeSource(Protocol):
    source_id: str
    authority: CreativeSourceAuthority

    async def fetch(self) -> CreativeSnapshot: ...
