from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


AWIN_API_BASE = "https://api.awin.com"


class AwinApiError(ValueError):
    """Safe, user-facing Awin API error without credential material."""


@dataclass(frozen=True, slots=True)
class AwinAccount:
    id: str
    name: str
    account_type: str
    user_role: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.account_type,
            "userRole": self.user_role,
        }


@dataclass(frozen=True, slots=True)
class AwinProgramme:
    id: str
    name: str
    relationship: str | None
    status: str | None
    logo_url: str | None
    description: str | None
    country_code: str | None
    currency_code: str | None
    click_through_url: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "relationship": self.relationship,
            "status": self.status,
            "logoUrl": self.logo_url,
            "description": self.description,
            "countryCode": self.country_code,
            "currencyCode": self.currency_code,
            "clickThroughUrl": self.click_through_url,
        }


def _text(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _objects(payload: Any, *, label: str) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, Mapping):
        if isinstance(payload.get("accounts"), list):
            rows = payload["accounts"]
        elif isinstance(payload.get("programmes"), list):
            rows = payload["programmes"]
        elif isinstance(payload.get("programs"), list):
            rows = payload["programs"]
        elif "accountId" in payload or "id" in payload:
            rows = [payload]
        else:
            raise AwinApiError(f"Awin returned an unexpected {label} response.")
    else:
        raise AwinApiError(f"Awin returned an unexpected {label} response.")
    if any(not isinstance(row, Mapping) for row in rows):
        raise AwinApiError(f"Awin returned malformed {label} data.")
    return list(rows)


class AwinClient:
    def __init__(self, http) -> None:
        self.http = http

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        value = str(token).strip()
        if not value:
            raise AwinApiError("An Awin access token is required.")
        return {
            "Authorization": f"Bearer {value}",
            "Accept": "application/json",
        }

    @staticmethod
    def _raise_for_status(status: int) -> None:
        if status in {401, 403}:
            raise AwinApiError(
                "Awin rejected the access token or the account permission is insufficient."
            )
        if status == 429:
            raise AwinApiError("Awin rate limit reached. Please try again later.")
        if status < 200 or status >= 300:
            raise AwinApiError(f"Awin API request failed with HTTP {status}.")

    async def accounts(self, *, token: str) -> list[AwinAccount]:
        response = await self.http.request(
            method="GET",
            url=f"{AWIN_API_BASE}/accounts",
            headers=self._headers(token),
            query={"type": "publisher"},
        )
        self._raise_for_status(response.status)
        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise AwinApiError("Awin returned an invalid account response.") from exc

        accounts: list[AwinAccount] = []
        for row in _objects(payload, label="account"):
            account_id = _text(row.get("accountId") or row.get("id"))
            account_type = (_text(row.get("accountType") or row.get("type")) or "").lower()
            if not account_id:
                raise AwinApiError("Awin returned an account without an ID.")
            if account_type and account_type != "publisher":
                continue
            accounts.append(
                AwinAccount(
                    id=account_id,
                    name=_text(row.get("accountName") or row.get("name")) or f"Publisher {account_id}",
                    account_type="publisher",
                    user_role=_text(row.get("userRole")),
                )
            )
        return accounts

    async def programmes(
        self,
        *,
        token: str,
        publisher_id: str,
        relationship: str | None = None,
    ) -> list[AwinProgramme]:
        publisher = str(publisher_id).strip()
        if not publisher:
            raise AwinApiError("A publisher account must be selected first.")
        query: dict[str, str] = {}
        if relationship:
            query["relationship"] = relationship
        response = await self.http.request(
            method="GET",
            url=f"{AWIN_API_BASE}/publishers/{publisher}/programmes",
            headers=self._headers(token),
            query=query or None,
        )
        self._raise_for_status(response.status)
        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise AwinApiError("Awin returned an invalid programme response.") from exc

        result: list[AwinProgramme] = []
        for row in _objects(payload, label="programme"):
            programme_id = _text(row.get("id"))
            if not programme_id:
                raise AwinApiError("Awin returned a programme without an ID.")
            region = row.get("primaryRegion")
            country = _text(region.get("countryCode")) if isinstance(region, Mapping) else None
            result.append(
                AwinProgramme(
                    id=programme_id,
                    name=_text(row.get("name")) or f"Advertiser {programme_id}",
                    relationship=_text(row.get("relationship")),
                    status=_text(row.get("status")),
                    logo_url=_text(row.get("logoUrl")),
                    description=_text(row.get("description")),
                    country_code=country,
                    currency_code=_text(row.get("currencyCode")),
                    click_through_url=_text(row.get("clickThroughUrl")),
                )
            )
        return result
