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

SKILL_ID = "awin-affiliate"
STORAGE_KEY = "creatives.v1"
LIST_CREATIVES_API = "awin-affiliate.creatives.list.v1"
IMPORT_HTML_API = "awin-affiliate.creatives.import-html.v1"
DESCRIBE_API = "awin-affiliate.describe.v1"


class AwinAffiliateSkill:
    manifest = SkillManifest(
        id=SKILL_ID,
        name="Awin Affiliate",
        version="0.1.0",
        runtime_api_version="1",
        description="Import and manage Awin affiliate creatives without depending on another Skill.",
        author="GamerHQ",
        permissions=(
            SkillCapability.STORAGE_SKILL.value,
            SkillCapability.AUDIT_WRITE.value,
        ),
        management_apis=SkillManagementApis(
            exposes=(
                ManagementApiContract(LIST_CREATIVES_API, "List imported Awin creatives."),
                ManagementApiContract(IMPORT_HTML_API, "Import supported Awin image creative HTML."),
                ManagementApiContract(DESCRIBE_API, "Describe current Awin Affiliate capabilities and limitations."),
            )
        ),
    )

    def __init__(self) -> None:
        self._manual_source = AwinHtmlCreativeSource()

    async def register(self, ctx) -> None:
        ctx.management.expose(LIST_CREATIVES_API, self._manage_list_creatives)
        ctx.management.expose(IMPORT_HTML_API, self._manage_import_html)
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
        return SkillHealth("PASS", f"{len(creatives)} Awin creative(s) in the local library.")

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
                merged = Creative(
                    **{
                        **candidate.__dict__,
                        "user_enabled": existing.user_enabled,
                        "first_seen_at": existing.first_seen_at,
                    }
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
                }
            ],
            "limitations": [
                "Authenticated Awin API sync is not enabled in this slice.",
                "Manual imports do not mark omitted creatives as missing because a pasted snippet may be incomplete.",
            ],
        }
