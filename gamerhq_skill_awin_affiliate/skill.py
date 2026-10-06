from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from skill_runtime import (
    ManagementApiContract,
    SkillCapability,
    SkillHealth,
    SkillManagementApis,
    SkillManifest,
)

from .imports import AwinHtmlCreativeSource
from .models import Creative
from .setup import AwinSetupService
from .creative_sources import CreativeSnapshot
from .sync import CreativeSyncResult, apply_creative_snapshot

SKILL_ID = "awin-affiliate"
STORAGE_KEY = "creatives.v1"
LIST_CREATIVES_API = "awin-affiliate.creatives.list.v1"
IMPORT_HTML_API = "awin-affiliate.creatives.import-html.v1"
DESCRIBE_API = "awin-affiliate.describe.v1"
SETUP_STATUS_API = "awin-affiliate.setup.status.v1"
SETUP_CONNECT_API = "awin-affiliate.setup.connect.v1"
SETUP_ACCOUNTS_API = "awin-affiliate.setup.accounts.v1"
SETUP_SELECT_PUBLISHER_API = "awin-affiliate.setup.select-publisher.v1"
SETUP_DISCONNECT_API = "awin-affiliate.setup.disconnect.v1"
ADVERTISERS_LIST_API = "awin-affiliate.advertisers.list.v1"


class AwinAffiliateSkill:
    manifest = SkillManifest(
        id=SKILL_ID,
        name="Awin Affiliate",
        version="0.2.0",
        runtime_api_version="1",
        description="Import and manage Awin affiliate creatives without depending on another Skill.",
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
                ManagementApiContract(DESCRIBE_API, "Describe current Awin Affiliate capabilities and limitations."),
                ManagementApiContract(SETUP_STATUS_API, "Read masked Awin connection status."),
                ManagementApiContract(SETUP_CONNECT_API, "Verify and securely store an Awin access token."),
                ManagementApiContract(SETUP_ACCOUNTS_API, "List publisher accounts available to the connected Awin user."),
                ManagementApiContract(SETUP_SELECT_PUBLISHER_API, "Select the publisher account used by this guild."),
                ManagementApiContract(SETUP_DISCONNECT_API, "Disconnect the Awin account and delete the stored token."),
                ManagementApiContract(ADVERTISERS_LIST_API, "List Awin programmes/advertisers for the selected publisher."),
            )
        ),
    )

    def __init__(self) -> None:
        self._manual_source = AwinHtmlCreativeSource()

    async def register(self, ctx) -> None:
        ctx.management.expose(LIST_CREATIVES_API, self._manage_list_creatives)
        ctx.management.expose(IMPORT_HTML_API, self._manage_import_html)
        ctx.management.expose(DESCRIBE_API, self._manage_describe)
        ctx.management.expose(SETUP_STATUS_API, self._manage_setup_status)
        ctx.management.expose(SETUP_CONNECT_API, self._manage_setup_connect)
        ctx.management.expose(SETUP_ACCOUNTS_API, self._manage_setup_accounts)
        ctx.management.expose(SETUP_SELECT_PUBLISHER_API, self._manage_setup_select_publisher)
        ctx.management.expose(SETUP_DISCONNECT_API, self._manage_setup_disconnect)
        ctx.management.expose(ADVERTISERS_LIST_API, self._manage_advertisers_list)

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
        status = await AwinSetupService(ctx).status()
        if not status["connected"]:
            return SkillHealth("PASS", f"Awin not connected; {len(creatives)} local creative(s).")
        if not status["publisherSelected"]:
            return SkillHealth("PASS", f"Awin connected; publisher selection required; {len(creatives)} local creative(s).")
        publisher = status["publisher"] or {}
        return SkillHealth(
            "PASS",
            f"Awin connected to {publisher.get('name') or publisher.get('id')}; {len(creatives)} local creative(s).",
        )

    async def list_creatives(self, ctx) -> list[Creative]:
        raw = await ctx.storage.get(STORAGE_KEY)
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise ValueError("Stored Awin Creative Library is invalid.")
        return [Creative.from_dict(item) for item in raw]

    async def sync_snapshot(
        self,
        ctx,
        *,
        snapshot: CreativeSnapshot,
        now: int | None = None,
    ) -> CreativeSyncResult:
        timestamp = int(time.time()) if now is None else int(now)
        ordered, result = apply_creative_snapshot(
            await self.list_creatives(ctx),
            snapshot,
            now=timestamp,
        )
        await ctx.storage.set(STORAGE_KEY, [creative.to_dict() for creative in ordered])
        await ctx.audit.write(
            action="creatives.synced",
            target=snapshot.advertiser_id,
            metadata={
                "source": snapshot.source_id,
                "authority": snapshot.authority.value,
                "found": result.found,
                "new": result.new,
                "updated": result.updated,
                "missing": result.missing,
                "restored": result.restored,
                "unchanged": result.unchanged,
            },
        )
        return result

    async def import_html(
        self,
        ctx,
        *,
        html: str,
        advertiser_name: str | None = None,
        now: int | None = None,
    ) -> dict[str, Any]:
        snapshot = self._manual_source.snapshot(html, advertiser_name=advertiser_name)
        sync = await self.sync_snapshot(ctx, snapshot=snapshot, now=now)
        await ctx.audit.write(
            action="creatives.imported",
            target=advertiser_name or snapshot.advertiser_id,
            metadata={
                "source": snapshot.source_id,
                "new": sync.new,
                "updated": sync.updated,
                "unchanged": sync.unchanged,
            },
        )
        return {
            **sync.to_dict(),
            "added": sync.new,
            "creativeIds": [creative.id for creative in snapshot.creatives],
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
        return {"setup": await AwinSetupService(ctx).status()}

    async def _manage_setup_connect(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        token = str(payload.get("accessToken", "")).strip()
        if not token:
            raise ValueError("accessToken is required.")
        return {"setup": await AwinSetupService(ctx).connect(token=token)}

    async def _manage_setup_accounts(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        accounts = await AwinSetupService(ctx).publisher_accounts()
        return {"accounts": [account.to_dict() for account in accounts]}

    async def _manage_setup_select_publisher(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        publisher_id = str(payload.get("publisherId", "")).strip()
        if not publisher_id:
            raise ValueError("publisherId is required.")
        return await AwinSetupService(ctx).select_publisher(publisher_id=publisher_id)

    async def _manage_setup_disconnect(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        await AwinSetupService(ctx).disconnect()
        return {"disconnected": True}

    async def _manage_advertisers_list(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        relationship = payload.get("relationship")
        if relationship is not None:
            relationship = str(relationship).strip().lower() or None
        allowed = {None, "joined", "pending", "suspended", "rejected", "notjoined"}
        if relationship not in allowed:
            raise ValueError("Unsupported Awin relationship filter.")
        programmes = await AwinSetupService(ctx).programmes(relationship=relationship)
        return {"advertisers": [programme.to_dict() for programme in programmes]}

    async def _manage_describe(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {
            "skillId": SKILL_ID,
            "standalone": True,
            "requiresRecurringPosts": False,
            "availableSources": [
                {
                    "id": "manual_html",
                    "label": "Awin HTML",
                    "networkRequired": False,
                    "credentialsRequired": False,
                    "supportsMissingDetection": False,
                },
                {
                    "id": "awin_api",
                    "label": "Awin Publisher API",
                    "networkRequired": True,
                    "credentialsRequired": True,
                    "supportsAccountDiscovery": True,
                    "supportsAdvertiserDiscovery": True,
                    "supportsMissingDetection": False,
                },
            ],
            "limitations": [
                "A complete official image-creative library endpoint has not been established yet.",
                "Manual imports do not mark omitted creatives as missing because a pasted snippet may be incomplete.",
            ],
        }
