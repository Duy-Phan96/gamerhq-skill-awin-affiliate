from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .awin_api import AwinAccount, AwinClient, AwinProgramme


SETTINGS_KEY = "settings.v1"
ACCESS_TOKEN_SECRET = "awin-access-token.v1"


@dataclass(frozen=True, slots=True)
class AwinSettings:
    publisher_id: str | None = None
    publisher_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "publisherId": self.publisher_id,
            "publisherName": self.publisher_name,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AwinSettings":
        publisher_id = value.get("publisherId")
        publisher_name = value.get("publisherName")
        return cls(
            publisher_id=str(publisher_id).strip() if publisher_id else None,
            publisher_name=str(publisher_name).strip() if publisher_name else None,
        )


class AwinSetupService:
    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.client = AwinClient(ctx.http)

    async def settings(self) -> AwinSettings:
        raw = await self.ctx.storage.get(SETTINGS_KEY)
        if raw is None:
            return AwinSettings()
        if not isinstance(raw, Mapping):
            raise ValueError("Stored Awin settings are invalid.")
        return AwinSettings.from_dict(raw)

    async def status(self) -> dict[str, Any]:
        settings = await self.settings()
        token = await self.ctx.secrets.get(ACCESS_TOKEN_SECRET)
        connected = bool(token)
        return {
            "connected": connected,
            "publisherSelected": bool(settings.publisher_id),
            "publisher": (
                {
                    "id": settings.publisher_id,
                    "name": settings.publisher_name,
                }
                if settings.publisher_id
                else None
            ),
            "token": "••••••••" if connected else None,
        }

    async def connect(self, *, token: str) -> dict[str, Any]:
        supplied = str(token).strip()
        accounts = await self.client.accounts(token=supplied)
        if not accounts:
            raise ValueError("No Awin publisher account is available for this token.")

        # Persist only after the token has been verified successfully.
        await self.ctx.secrets.set(ACCESS_TOKEN_SECRET, supplied)

        if len(accounts) == 1:
            selected = accounts[0]
            await self.ctx.storage.set(
                SETTINGS_KEY,
                AwinSettings(
                    publisher_id=selected.id,
                    publisher_name=selected.name,
                ).to_dict(),
            )
            selection_required = False
        else:
            previous = await self.settings()
            matching = next((item for item in accounts if item.id == previous.publisher_id), None)
            if matching:
                await self.ctx.storage.set(
                    SETTINGS_KEY,
                    AwinSettings(
                        publisher_id=matching.id,
                        publisher_name=matching.name,
                    ).to_dict(),
                )
            else:
                await self.ctx.storage.set(SETTINGS_KEY, AwinSettings().to_dict())
            selection_required = matching is None

        await self.ctx.audit.write(
            action="awin.connected",
            metadata={
                "publisherAccounts": len(accounts),
                "selectionRequired": selection_required,
            },
        )
        return {
            "connected": True,
            "selectionRequired": selection_required,
            "accounts": [account.to_dict() for account in accounts],
            "publisher": (await self.status())["publisher"],
        }

    async def publisher_accounts(self) -> list[AwinAccount]:
        token = await self.ctx.secrets.get(ACCESS_TOKEN_SECRET)
        if not token:
            raise ValueError("Connect an Awin account first.")
        return await self.client.accounts(token=token)

    async def select_publisher(self, *, publisher_id: str) -> dict[str, Any]:
        requested = str(publisher_id).strip()
        accounts = await self.publisher_accounts()
        selected = next((item for item in accounts if item.id == requested), None)
        if selected is None:
            raise ValueError("Selected publisher account is not available to the connected Awin user.")
        settings = AwinSettings(
            publisher_id=selected.id,
            publisher_name=selected.name,
        )
        await self.ctx.storage.set(SETTINGS_KEY, settings.to_dict())
        await self.ctx.audit.write(
            action="awin.publisher-selected",
            target=selected.id,
            metadata={"publisherName": selected.name},
        )
        return {"publisher": {"id": selected.id, "name": selected.name}}

    async def programmes(self, *, relationship: str | None = None) -> list[AwinProgramme]:
        token = await self.ctx.secrets.get(ACCESS_TOKEN_SECRET)
        if not token:
            raise ValueError("Connect an Awin account first.")
        settings = await self.settings()
        if not settings.publisher_id:
            raise ValueError("Select an Awin publisher account first.")
        return await self.client.programmes(
            token=token,
            publisher_id=settings.publisher_id,
            relationship=relationship,
        )

    async def disconnect(self) -> None:
        await self.ctx.secrets.delete(ACCESS_TOKEN_SECRET)
        await self.ctx.storage.set(SETTINGS_KEY, AwinSettings().to_dict())
        await self.ctx.audit.write(action="awin.disconnected")
