from __future__ import annotations

import asyncio
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

from .creative_library import (
    MAX_BULK_IDS,
    list_page as creative_list_page,
    management_view as creative_management_view,
    preview_view as creative_preview_view,
    set_enabled as set_creatives_enabled,
)
from .imports import AwinHtmlCreativeSource
from .models import Creative
from .setup import AwinSetupService

SKILL_ID = "awin-affiliate"
STORAGE_KEY = "creatives.v1"
LIST_CREATIVES_API = "awin-affiliate.creatives.list.v1"
GET_CREATIVE_API = "awin-affiliate.creatives.get.v1"
PREVIEW_CREATIVE_API = "awin-affiliate.creatives.preview.v1"
SET_CREATIVES_ENABLED_API = "awin-affiliate.creatives.set-enabled.v1"
SET_ADVERTISER_CREATIVES_ENABLED_API = "awin-affiliate.creatives.set-advertiser-enabled.v1"
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
        version="0.3.0",
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
                ManagementApiContract(LIST_CREATIVES_API, "List and filter imported Awin creatives."),
                ManagementApiContract(GET_CREATIVE_API, "Read one Awin creative."),
                ManagementApiContract(PREVIEW_CREATIVE_API, "Build a Discord-native preview for one Awin creative."),
                ManagementApiContract(SET_CREATIVES_ENABLED_API, "Enable or disable selected Awin creatives."),
                ManagementApiContract(SET_ADVERTISER_CREATIVES_ENABLED_API, "Enable or disable all matching creatives for one advertiser."),
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
        self._creative_locks: dict[int, asyncio.Lock] = {}

    def _creative_lock(self, guild_id: int) -> asyncio.Lock:
        return self._creative_locks.setdefault(guild_id, asyncio.Lock())

    async def register(self, ctx) -> None:
        ctx.management.expose(LIST_CREATIVES_API, self._manage_list_creatives)
        ctx.management.expose(GET_CREATIVE_API, self._manage_get_creative)
        ctx.management.expose(PREVIEW_CREATIVE_API, self._manage_preview_creative)
        ctx.management.expose(SET_CREATIVES_ENABLED_API, self._manage_set_creatives_enabled)
        ctx.management.expose(SET_ADVERTISER_CREATIVES_ENABLED_API, self._manage_set_advertiser_creatives_enabled)
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
        async with self._creative_lock(ctx.guild_id):
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
        advertiser_id = str(payload.get("advertiserId", "")).strip() or None
        creative_type = str(payload.get("type", "")).strip() or None
        enabled_only = payload.get("enabledOnly", False)
        active_only = payload.get("activeOnly", False)
        if not isinstance(enabled_only, bool) or not isinstance(active_only, bool):
            raise ValueError("enabledOnly and activeOnly must be booleans.")
        try:
            offset = int(payload.get("offset", 0))
            limit = int(payload.get("limit", 25))
        except (TypeError, ValueError) as exc:
            raise ValueError("offset and limit must be integers.") from exc
        page = creative_list_page(
            await self.list_creatives(ctx),
            advertiser_id=advertiser_id,
            enabled_only=enabled_only,
            active_only=active_only,
            creative_type=creative_type,
            offset=offset,
            limit=limit,
        )
        return {"creatives": page}

    async def _creative_by_id(self, ctx, creative_id: str) -> Creative:
        requested = str(creative_id).strip()
        if not requested:
            raise ValueError("creativeId is required.")
        creative = next((item for item in await self.list_creatives(ctx) if item.id == requested), None)
        if creative is None:
            raise ValueError("Creative was not found.")
        return creative

    async def _manage_get_creative(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        creative = await self._creative_by_id(ctx, str(payload.get("creativeId", "")))
        return {"creative": creative_management_view(creative)}

    async def _manage_preview_creative(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        creative = await self._creative_by_id(ctx, str(payload.get("creativeId", "")))
        return creative_preview_view(creative)

    async def _manage_set_creatives_enabled(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        enabled = payload.get("enabled")
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be a boolean.")
        raw_ids = payload.get("creativeIds")
        if isinstance(raw_ids, str):
            creative_ids = [raw_ids]
        elif isinstance(raw_ids, list):
            creative_ids = raw_ids
        else:
            single = str(payload.get("creativeId", "")).strip()
            creative_ids = [single] if single else []
        if len(creative_ids) > MAX_BULK_IDS:
            raise ValueError(f"At most {MAX_BULK_IDS} creative IDs can be changed at once.")

        async with self._creative_lock(ctx.guild_id):
            creatives = await self.list_creatives(ctx)
            try:
                updated, changed = set_creatives_enabled(
                    creatives,
                    creative_ids=creative_ids,
                    enabled=enabled,
                )
            except KeyError as exc:
                raise ValueError(str(exc).strip("'")) from exc
            await ctx.storage.set(STORAGE_KEY, [creative.to_dict() for creative in updated])

        await ctx.audit.write(
            action="creatives.enabled-changed",
            metadata={"requested": len(creative_ids), "changed": changed, "enabled": enabled},
        )
        return {
            "updated": len(creative_ids),
            "changed": changed,
            "enabled": enabled,
        }

    async def _manage_set_advertiser_creatives_enabled(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        advertiser_id = str(payload.get("advertiserId", "")).strip()
        enabled = payload.get("enabled")
        active_only = payload.get("activeOnly", False)
        if not advertiser_id:
            raise ValueError("advertiserId is required.")
        if not isinstance(enabled, bool) or not isinstance(active_only, bool):
            raise ValueError("enabled and activeOnly must be booleans.")

        async with self._creative_lock(ctx.guild_id):
            creatives = await self.list_creatives(ctx)
            matching = [
                creative.id
                for creative in creatives
                if creative.advertiser_id == advertiser_id
                and (not active_only or creative.state.value in {"ACTIVE", "NEW"})
            ]
            if not matching:
                return {"updated": 0, "changed": 0, "enabled": enabled}
            updated, changed = set_creatives_enabled(
                creatives,
                creative_ids=matching,
                enabled=enabled,
            )
            await ctx.storage.set(STORAGE_KEY, [creative.to_dict() for creative in updated])

        await ctx.audit.write(
            action="creatives.advertiser-enabled-changed",
            target=advertiser_id,
            metadata={"requested": len(matching), "changed": changed, "enabled": enabled},
        )
        return {
            "updated": len(matching),
            "changed": changed,
            "enabled": enabled,
        }

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
