from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping


class ConnectionStatus(StrEnum):
    NOT_CONNECTED = "NOT_CONNECTED"
    PUBLISHER_SELECTION_REQUIRED = "PUBLISHER_SELECTION_REQUIRED"
    CONNECTED = "CONNECTED"


@dataclass(frozen=True, slots=True)
class AwinConnection:
    status: ConnectionStatus
    publisher_id: str | None = None
    publisher_name: str | None = None
    user_role: str | None = None
    available_publishers: tuple[Mapping[str, Any], ...] = ()
    last_verified_at: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "publisherId": self.publisher_id,
            "publisherName": self.publisher_name,
            "userRole": self.user_role,
            "availablePublishers": [dict(item) for item in self.available_publishers],
            "lastVerifiedAt": self.last_verified_at,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AwinConnection":
        try:
            raw_available = value.get("availablePublishers", ())
            if not isinstance(raw_available, (list, tuple)):
                raise TypeError
            return cls(
                status=ConnectionStatus(str(value["status"])),
                publisher_id=_optional_str(value.get("publisherId")),
                publisher_name=_optional_str(value.get("publisherName")),
                user_role=_optional_str(value.get("userRole")),
                available_publishers=tuple(dict(item) for item in raw_available),
                last_verified_at=_optional_int(value.get("lastVerifiedAt")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Stored Awin connection configuration is invalid.") from exc


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
