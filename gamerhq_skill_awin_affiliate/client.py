from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from skill_runtime import TransientHostError


AWIN_API_BASE = "https://api.awin.com"


class AwinApiError(ValueError):
    """Safe provider-facing error suitable for management surfaces."""


@dataclass(frozen=True, slots=True)
class PublisherAccount:
    id: str
    name: str
    user_role: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "publisherId": self.id,
            "name": self.name,
            "userRole": self.user_role,
        }


class AwinApiClient:
    def __init__(self, http) -> None:
        self._http = http

    async def publisher_accounts(self, *, access_token: str) -> list[PublisherAccount]:
        token = str(access_token).strip()
        if not token:
            raise AwinApiError("Awin access token is required.")

        try:
            response = await self._http.request(
                method="GET",
                url=f"{AWIN_API_BASE}/accounts",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                query={"type": "publisher"},
            )
        except TransientHostError as exc:
            raise AwinApiError("Could not reach the Awin API. Try again shortly.") from exc
        if response.status in {401, 403}:
            raise AwinApiError(
                "Awin rejected the access token or the account permissions. "
                "Check the token and your Awin user access."
            )
        if response.status == 429:
            raise AwinApiError("Awin API rate limit reached. Try again shortly.")
        if response.status >= 500:
            raise AwinApiError("Awin API is temporarily unavailable.")
        if response.status != 200:
            raise AwinApiError(f"Awin connection test failed with HTTP {response.status}.")

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise AwinApiError("Awin returned an invalid accounts response.") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("accounts"), list):
            raise AwinApiError("Awin returned an unexpected accounts response.")

        accounts: list[PublisherAccount] = []
        seen: set[str] = set()
        for raw in payload["accounts"]:
            if not isinstance(raw, dict):
                continue
            if str(raw.get("accountType", "")).lower() != "publisher":
                continue
            try:
                account_id = str(int(raw["accountId"]))
            except (KeyError, TypeError, ValueError):
                continue
            if int(account_id) <= 0 or account_id in seen:
                continue
            seen.add(account_id)
            name = str(raw.get("accountName", "")).strip() or f"Publisher {account_id}"
            role = str(raw.get("userRole", "")).strip() or None
            accounts.append(PublisherAccount(account_id, name, role))

        accounts.sort(key=lambda item: (item.name.casefold(), int(item.id)))
        return accounts
