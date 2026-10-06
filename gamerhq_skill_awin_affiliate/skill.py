from __future__ import annotations

import time
from dataclasses import replace
from collections.abc import Mapping
from typing import Any

from skill_runtime import (
    ManagementApiContract,
    SkillCapability,
    SkillHealth,
    SkillManagementApis,
    SkillManifest,
)

from .client import AwinApiClient, PublisherAccount
from .connection import AwinConnection, ConnectionStatus
from .imports import AwinHtmlCreativeSource
from .models import Creative

SKILL_ID = "awin-affiliate"
STORAGE_KEY = "creatives.v1"
CONNECTION_STORAGE_KEY = "connection.v1"
ACCESS_TOKEN_SECRET_KEY = "access-token.v1"

LIST_CREATIVES_API = "awin-affiliate.creatives.list.v1"
IMPORT_HTML_API = "awin-affiliate.creatives.import-html.v1"
SETUP_STATUS_API = "awin-affiliate.setup.status.v1"
SETUP_CONNECT_API = "awin-affiliate.setup.connect.v1"
SETUP_SELECT_PUBLISHER_API = "awin-affiliate.setup.select-publisher.v1"
SETUP_DISCONNECT_API = "awin-affiliate.setup.disconnect.v1"
DESCRIBE_API = "awin-affiliate.describe.v1"


class AwinAffiliateSkill:
    manifest = SkillManifest(
        id=SKILL_ID,
        name="Awin Affiliate",
        version="0.2.0",
        runtime_api_version="1",
        description="Connect Awin, import creatives and manage affiliate content without depending on another Skill.",
        author="GamerHQ",
        permissions=(
            SkillCapability.STORAGE_SKILL.value,
            SkillCapability.SKILL_SECURE_STORAGE.value,
            SkillCapability.HTTP_EXTERNAL.value,
            SkillCapability.AUDIT_WRITE.value,
        ),
        management_apis=SkillManagementApis(
            exposes=(
                ManagementApiContract(LIST_CREATIVES_API, "List imported Awin creatives."),
                ManagementApiContract(IMPORT_HTML_API, "Import supported Awin image creative HTML."),
                ManagementApiContract(SETUP_STATUS_API, "Read safe Awin connection status."),
                ManagementApiContract(SETUP_CONNECT_API, "Validate and connect an Awin user access token."),
                ManagementApiContract(SETUP_SELECT_PUBLISHER_API, "Select one accessible Awin publisher account."),
                ManagementApiContract(SETUP_DISCONNECT_API, "Remove the stored Awin connection."),
                ManagementApiContract(DESCRIBE_API, "Describe current Awin Affiliate capabilities and limitations."),
            )
        ),
    )

    def __init__(self) -> None:
        self._manual_source = AwinHtmlCreativeSource()

    async def register(self, ctx) -> None:
        ctx.management.expose(LIST_CREATIVES_API, self._manage_list_creatives)
        ctx.management.expose(IMPORT_HTML_API, self._manage_import_html)
        ctx.management.expose(SETUP_STATUS_API, self._manage_setup_status)
        ctx.management.expose(SETUP_CONNECT_API, self._manage_setup_connect)
        ctx.management.expose(SETUP_SELECT_PUBLISHER_API, self._manage_setup_select_publisher)
        ctx.management.expose(SETUP_DISCONNECT_API, self._manage_setup_disconnect)
        ctx.management.expose(DESCRIBE_API, self._manage_describe)

    async def enable(self, ctx) -> None:
        await ctx.audit.write(action="enabled")

    async def disable(self, ctx) -> None:
        await ctx.audit.write(action="disabled")

    async def start(self, ctx) -> None:
        return None

    async def stop(self, ctx) -> None:
        return None

    async def health_check(self, ctx) -> SkillHealth:
        creatives = await self.list_creatives(ctx)
        connection = await self.connection(ctx)
        if connection.status == ConnectionStatus.CONNECTED:
            detail = f"Connected to publisher {connection.publisher_id}; {len(creatives)} creative(s) in the local library."
        elif connection.status == ConnectionStatus.PUBLISHER_SELECTION_REQUIRED:
            detail = f"Awin token verified; publisher selection required; {len(creatives)} creative(s) imported."
        else:
            detail = f"Awin account not connected; {len(creatives)} creative(s) in the local library."
        return SkillHealth("PASS", detail)

    async def connection(self, ctx) -> AwinConnection:
        raw = await ctx.storage.get(CONNECTION_STORAGE_KEY)
        if raw is None:
            return AwinConnection(ConnectionStatus.NOT_CONNECTED)
        if not isinstance(raw, Mapping):
            raise ValueError("Stored Awin connection configuration is invalid.")
        return AwinConnection.from_dict(raw)

    async def _save_connection(self, ctx, connection: AwinConnection) -> None:
        await ctx.storage.set(CONNECTION_STORAGE_KEY, connection.to_dict())

    @staticmethod
    def _select_account(accounts: list[PublisherAccount], publisher_id: str) -> PublisherAccount:
        requested = str(publisher_id).strip()
        for account in accounts:
            if account.id == requested:
                return account
        raise ValueError("Selected Awin publisher account is not available to this token.")

    async def connect(
        self,
        ctx,
        *,
        access_token: str,
        publisher_id: str | None = None,
        now: int | None = None,
    ) -> AwinConnection:
        token = str(access_token).strip()
        if not token:
            raise ValueError("Awin access token is required.")

        accounts = await AwinApiClient(ctx.http).publisher_accounts(access_token=token)
        if not accounts:
            raise ValueError("No Awin publisher accounts are available to this user.")

        timestamp = int(time.time()) if now is None else int(now)
        requested = str(publisher_id).strip() if publisher_id is not None else ""
        if requested:
            selected = self._select_account(accounts, requested)
            connection = AwinConnection(
                status=ConnectionStatus.CONNECTED,
                publisher_id=selected.id,
                publisher_name=selected.name,
                user_role=selected.user_role,
                last_verified_at=timestamp,
            )
        elif len(accounts) == 1:
            selected = accounts[0]
            connection = AwinConnection(
                status=ConnectionStatus.CONNECTED,
                publisher_id=selected.id,
                publisher_name=selected.name,
                user_role=selected.user_role,
                last_verified_at=timestamp,
            )
        else:
            connection = AwinConnection(
                status=ConnectionStatus.PUBLISHER_SELECTION_REQUIRED,
                available_publishers=tuple(account.to_dict() for account in accounts),
                last_verified_at=timestamp,
            )

        # Persist the token only after Awin has accepted it and the response has
        # been normalized successfully. It is never copied into Skill Storage.
        await ctx.secrets.set(ACCESS_TOKEN_SECRET_KEY, token)
        await self._save_connection(ctx, connection)
        await ctx.audit.write(
            action=(
                "account.connected"
                if connection.status == ConnectionStatus.CONNECTED
                else "account.publisher-selection-required"
            ),
            target=connection.publisher_id,
            metadata={"publisherCount": len(accounts)},
        )
        return connection

    async def select_publisher(
        self,
        ctx,
        *,
        publisher_id: str,
        now: int | None = None,
    ) -> AwinConnection:
        token = await ctx.secrets.get(ACCESS_TOKEN_SECRET_KEY)
        if not token:
            raise ValueError("Connect an Awin account before selecting a publisher.")

        accounts = await AwinApiClient(ctx.http).publisher_accounts(access_token=token)
        selected = self._select_account(accounts, publisher_id)
        timestamp = int(time.time()) if now is None else int(now)
        connection = AwinConnection(
            status=ConnectionStatus.CONNECTED,
            publisher_id=selected.id,
            publisher_name=selected.name,
            user_role=selected.user_role,
            last_verified_at=timestamp,
        )
        await self._save_connection(ctx, connection)
        await ctx.audit.write(
            action="account.publisher-selected",
            target=selected.id,
        )
        return connection

    async def disconnect(self, ctx) -> None:
        await ctx.secrets.delete(ACCESS_TOKEN_SECRET_KEY)
        await ctx.storage.delete(CONNECTION_STORAGE_KEY)
        await ctx.audit.write(action="account.disconnected")

    async def connection_view(self, ctx) -> dict[str, Any]:
        connection = await self.connection(ctx)
        token_configured = await ctx.secrets.get(ACCESS_TOKEN_SECRET_KEY) is not None
        result = connection.to_dict()
        result["tokenConfigured"] = token_configured
        result["connectionReady"] = (
            token_configured and connection.status == ConnectionStatus.CONNECTED
        )
        return result

    async def list_creatives(self, ctx) -> list[Creative]:
        raw = await ctx.storage.get(STORAGE_KEY)
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise ValueError("Stored Awin Creative Library is invalid.")
        return [Creative.from_dict(item) for item in raw]

    async def import_html(
        self,
        ctx,
        *,
        html: str,
        advertiser_name: str | None = None,
        now: int | None = None,
    ) -> dict[str, Any]:
        timestamp = int(time.time()) if now is None else int(now)
        incoming = self._manual_source.parse(html, advertiser_name=advertiser_name)
        current = {creative.id: creative for creative in await self.list_creatives(ctx)}

        added = 0
        updated = 0
        imported_ids: list[str] = []
        for candidate in incoming:
            existing = current.get(candidate.id)
            if existing is None:
                current[candidate.id] = candidate.with_seen_at(timestamp)
                added += 1
            else:
                merged = replace(
                    candidate,
                    user_enabled=existing.user_enabled,
                    first_seen_at=existing.first_seen_at,
                ).with_seen_at(timestamp)
                current[candidate.id] = merged
                updated += 1
            imported_ids.append(candidate.id)

        ordered = sorted(current.values(), key=lambda creative: creative.id)
        await ctx.storage.set(STORAGE_KEY, [creative.to_dict() for creative in ordered])
        await ctx.audit.write(
            action="creatives.imported",
            target=advertiser_name,
            metadata={"source": "manual_html", "added": added, "updated": updated},
        )
        return {
            "source": "manual_html",
            "found": len(incoming),
            "added": added,
            "updated": updated,
            "total": len(ordered),
            "creativeIds": imported_ids,
        }

    async def _manage_list_creatives(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        creatives = await self.list_creatives(ctx)
        return {"creatives": [creative.to_dict() for creative in creatives]}

    async def _manage_import_html(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        html = payload.get("html")
        advertiser_name = payload.get("advertiserName")
        if advertiser_name is not None:
            advertiser_name = str(advertiser_name).strip() or None
        result = await self.import_html(
            ctx,
            html=str(html) if html is not None else "",
            advertiser_name=advertiser_name,
        )
        return {"import": result}

    async def _manage_setup_status(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"connection": await self.connection_view(ctx)}

    async def _manage_setup_connect(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        token = payload.get("accessToken")
        publisher_id = payload.get("publisherId")
        connection = await self.connect(
            ctx,
            access_token=str(token) if token is not None else "",
            publisher_id=str(publisher_id) if publisher_id is not None else None,
        )
        return {
            "connection": {
                **connection.to_dict(),
                "tokenConfigured": True,
                "connectionReady": connection.status == ConnectionStatus.CONNECTED,
            }
        }

    async def _manage_setup_select_publisher(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        publisher_id = str(payload.get("publisherId", "")).strip()
        if not publisher_id:
            raise ValueError("publisherId is required.")
        connection = await self.select_publisher(ctx, publisher_id=publisher_id)
        return {
            "connection": {
                **connection.to_dict(),
                "tokenConfigured": True,
                "connectionReady": True,
            }
        }

    async def _manage_setup_disconnect(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        await self.disconnect(ctx)
        return {
            "connection": {
                **AwinConnection(ConnectionStatus.NOT_CONNECTED).to_dict(),
                "tokenConfigured": False,
                "connectionReady": False,
            }
        }

    async def _manage_describe(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {
            "skillId": SKILL_ID,
            "standalone": True,
            "requiresRecurringPosts": False,
            "setup": {
                "authentication": "Awin user access token",
                "publisherDiscovery": True,
                "autoSelectSinglePublisher": True,
                "storesTokenInSecretStorage": True,
            },
            "availableSources": [
                {
                    "id": "manual_html",
                    "label": "Awin HTML",
                    "networkRequired": False,
                    "credentialsRequired": False,
                    "supportsMissingDetection": False,
                }
            ],
            "limitations": [
                "Authenticated creative-library synchronization is not enabled yet.",
                "Manual imports do not mark omitted creatives as missing because a pasted snippet may be incomplete.",
            ],
        }
