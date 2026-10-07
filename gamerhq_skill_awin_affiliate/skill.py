from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Mapping
from typing import Any

from skill_runtime import (
    ManagementApiContract,
    SkillCapability,
    SkillHealth,
    SkillManagementApis,
    SkillManifest,
)

from .campaigns import (
    CAMPAIGNS_KEY,
    CAMPAIGN_HANDLER_ID,
    CAMPAIGN_HISTORY_KEY,
    MAX_CAMPAIGNS,
    append_history,
    campaign_status,
    history_for_campaign,
    update_campaign,
    MIN_INTERVAL_SECONDS as CAMPAIGN_MIN_INTERVAL_SECONDS,
    Campaign,
    choose_campaign_creative,
    validate_campaign,
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
from .posting import (
    POST_STATE_KEY,
    read_last_creative_id,
    render_post,
    select_creative,
    with_last_creative,
)
from .setup import AwinSetupService
from .creative_sources import CreativeSnapshot
from .sync import CreativeSyncResult, apply_creative_snapshot

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
POST_PREVIEW_API = "awin-affiliate.post.preview.v1"
POST_SEND_API = "awin-affiliate.post.send.v1"
CAMPAIGN_LIST_API = "awin-affiliate.campaigns.list.v1"
CAMPAIGN_CREATE_API = "awin-affiliate.campaigns.create.v1"
CAMPAIGN_SET_ACTIVE_API = "awin-affiliate.campaigns.set-active.v1"
CAMPAIGN_DELETE_API = "awin-affiliate.campaigns.delete.v1"
CAMPAIGN_RUN_NOW_API = "awin-affiliate.campaigns.run-now.v1"
CAMPAIGN_GET_API = "awin-affiliate.campaigns.get.v1"
CAMPAIGN_UPDATE_API = "awin-affiliate.campaigns.update.v1"
CAMPAIGN_PREVIEW_NEXT_API = "awin-affiliate.campaigns.preview-next.v1"
CAMPAIGN_HISTORY_API = "awin-affiliate.campaigns.history.v1"


class AwinAffiliateSkill:
    manifest = SkillManifest(
        id=SKILL_ID,
        name="Awin Affiliate",
        version="0.7.0",
        runtime_api_version="1",
        description="Import and manage Awin affiliate creatives without depending on another Skill.",
        author="GamerHQ",
        permissions=(
            SkillCapability.STORAGE_SKILL.value,
            SkillCapability.SKILL_SECURE_STORAGE.value,
            SkillCapability.HTTP_EXTERNAL.value,
            SkillCapability.DISCORD_CHANNELS_READ.value,
            SkillCapability.DISCORD_MESSAGES_SEND.value,
            SkillCapability.DISCORD_EMBEDS_SEND.value,
            SkillCapability.SCHEDULER_JOBS.value,
            SkillCapability.AUDIT_WRITE.value,
        ),
        management_apis=SkillManagementApis(
            exposes=(
                ManagementApiContract(LIST_CREATIVES_API, "List and filter imported Awin creatives."),
                ManagementApiContract(GET_CREATIVE_API, "Read one Awin creative."),
                ManagementApiContract(PREVIEW_CREATIVE_API, "Build a Discord-native preview for one Awin creative."),
                ManagementApiContract(SET_CREATIVES_ENABLED_API, "Enable or disable selected Awin creatives."),
                ManagementApiContract(SET_ADVERTISER_CREATIVES_ENABLED_API, "Enable or disable matching creatives for one advertiser."),
                ManagementApiContract(IMPORT_HTML_API, "Import supported Awin image creative HTML."),
                ManagementApiContract(DESCRIBE_API, "Describe current Awin Affiliate capabilities and limitations."),
                ManagementApiContract(SETUP_STATUS_API, "Read masked Awin connection status."),
                ManagementApiContract(SETUP_CONNECT_API, "Verify and securely store an Awin access token."),
                ManagementApiContract(SETUP_ACCOUNTS_API, "List publisher accounts available to the connected Awin user."),
                ManagementApiContract(SETUP_SELECT_PUBLISHER_API, "Select the publisher account used by this guild."),
                ManagementApiContract(SETUP_DISCONNECT_API, "Disconnect the Awin account and delete the stored token."),
                ManagementApiContract(ADVERTISERS_LIST_API, "List Awin programmes/advertisers for the selected publisher."),
                ManagementApiContract(POST_PREVIEW_API, "Preview an Awin affiliate post without sending it."),
                ManagementApiContract(POST_SEND_API, "Send a previously reviewed Awin affiliate creative to Discord."),
                ManagementApiContract(CAMPAIGN_LIST_API, "List recurring Awin campaigns."),
                ManagementApiContract(CAMPAIGN_CREATE_API, "Create a recurring Awin campaign."),
                ManagementApiContract(CAMPAIGN_SET_ACTIVE_API, "Pause or resume an Awin campaign."),
                ManagementApiContract(CAMPAIGN_DELETE_API, "Delete an Awin campaign."),
                ManagementApiContract(CAMPAIGN_RUN_NOW_API, "Run an Awin campaign immediately."),
                ManagementApiContract(CAMPAIGN_GET_API, "Read one recurring Awin campaign with derived status."),
                ManagementApiContract(CAMPAIGN_UPDATE_API, "Edit a recurring Awin campaign without changing its stable ID."),
                ManagementApiContract(CAMPAIGN_PREVIEW_NEXT_API, "Preview the next eligible Creative for a campaign without mutating rotation state."),
                ManagementApiContract(CAMPAIGN_HISTORY_API, "Read bounded recent delivery history for one Awin campaign."),
            )
        ),
    )

    def __init__(self) -> None:
        self._manual_source = AwinHtmlCreativeSource()
        self._creative_locks: dict[int, asyncio.Lock] = {}
        self._campaign_locks: dict[tuple[int, str], asyncio.Lock] = {}

    def _creative_lock(self, guild_id: int) -> asyncio.Lock:
        return self._creative_locks.setdefault(guild_id, asyncio.Lock())

    def _campaign_lock(self, guild_id: int, campaign_id: str) -> asyncio.Lock:
        return self._campaign_locks.setdefault((guild_id, campaign_id), asyncio.Lock())

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
        ctx.management.expose(POST_PREVIEW_API, self._manage_post_preview)
        ctx.management.expose(POST_SEND_API, self._manage_post_send)
        ctx.management.expose(CAMPAIGN_LIST_API, self._manage_campaign_list)
        ctx.management.expose(CAMPAIGN_CREATE_API, self._manage_campaign_create)
        ctx.management.expose(CAMPAIGN_SET_ACTIVE_API, self._manage_campaign_set_active)
        ctx.management.expose(CAMPAIGN_DELETE_API, self._manage_campaign_delete)
        ctx.management.expose(CAMPAIGN_RUN_NOW_API, self._manage_campaign_run_now)
        ctx.management.expose(CAMPAIGN_GET_API, self._manage_campaign_get)
        ctx.management.expose(CAMPAIGN_UPDATE_API, self._manage_campaign_update)
        ctx.management.expose(CAMPAIGN_PREVIEW_NEXT_API, self._manage_campaign_preview_next)
        ctx.management.expose(CAMPAIGN_HISTORY_API, self._manage_campaign_history)
        ctx.scheduler.register_handler(CAMPAIGN_HANDLER_ID, self._execute_campaign)

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
        async with self._creative_lock(ctx.guild_id):
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
        return {
            "creatives": creative_list_page(
                await self.list_creatives(ctx),
                advertiser_id=advertiser_id,
                enabled_only=enabled_only,
                active_only=active_only,
                creative_type=creative_type,
                offset=offset,
                limit=limit,
            )
        }

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
        return {"updated": len(creative_ids), "changed": changed, "enabled": enabled}

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
        return {"updated": len(matching), "changed": changed, "enabled": enabled}

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

    async def _post_selection(self, ctx, payload: Mapping[str, Any]):
        mode = str(payload.get("selectionMode", "specific")).strip().lower()
        creative_id = str(payload.get("creativeId", "")).strip() or None
        advertiser_id = str(payload.get("advertiserId", "")).strip() or None
        if mode in {"random", "next"} and advertiser_id is None:
            raise ValueError("advertiserId is required for random or next selection.")
        state = await ctx.storage.get(POST_STATE_KEY)
        last_creative_id = (
            read_last_creative_id(state, advertiser_id=advertiser_id)
            if advertiser_id
            else None
        )
        return select_creative(
            await self.list_creatives(ctx),
            mode=mode,
            creative_id=creative_id,
            advertiser_id=advertiser_id,
            last_creative_id=last_creative_id,
        )

    async def _validated_post_channel(self, ctx, channel_id: int) -> int:
        if channel_id <= 0:
            raise ValueError("channelId must be positive.")
        channel = await ctx.discord.get_channel(channel_id=channel_id)
        if channel.kind not in {"text", "thread"}:
            raise ValueError("Awin posts require a text channel or thread.")
        return channel.id

    async def _manage_post_preview(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            channel_id = int(payload["channelId"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("channelId is required.") from exc
        channel_id = await self._validated_post_channel(ctx, channel_id)
        selection = await self._post_selection(ctx, payload)
        rendered = render_post(
            selection.creative,
            title=str(payload.get("title", "")).strip() or None,
            text=str(payload.get("text", "")).strip() or None,
        )
        return {
            "preview": {
                "channelId": channel_id,
                "selection": selection.to_dict(),
                **rendered,
            },
            "confirmPayload": {
                "channelId": channel_id,
                "creativeId": selection.creative.id,
                "selectionMode": selection.mode,
                "title": str(payload.get("title", "")).strip() or None,
                "text": str(payload.get("text", "")).strip() or None,
            },
        }

    async def _manage_post_send(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            channel_id = int(payload["channelId"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("channelId is required.") from exc
        channel_id = await self._validated_post_channel(ctx, channel_id)
        creative_id = str(payload.get("creativeId", "")).strip()
        if not creative_id:
            raise ValueError("creativeId is required after preview.")

        selection = select_creative(
            await self.list_creatives(ctx),
            mode="specific",
            creative_id=creative_id,
        )
        rendered = render_post(
            selection.creative,
            title=str(payload.get("title", "")).strip() or None,
            text=str(payload.get("text", "")).strip() or None,
        )
        message_id = await ctx.discord.send_message(
            channel_id=channel_id,
            content=rendered["content"],
            embed=rendered["embed"],
            allowed_mentions=None,
            link_buttons=rendered["linkButtons"],
        )

        async with self._creative_lock(ctx.guild_id):
            state = await ctx.storage.get(POST_STATE_KEY)
            await ctx.storage.set(
                POST_STATE_KEY,
                with_last_creative(
                    state,
                    advertiser_id=selection.creative.advertiser_id,
                    creative_id=selection.creative.id,
                ),
            )

        await ctx.audit.write(
            action="awin.post-sent",
            target=selection.creative.advertiser_id,
            metadata={
                "creativeId": selection.creative.id,
                "channelId": channel_id,
                "messageId": message_id,
            },
        )
        return {
            "sent": True,
            "messageId": message_id,
            "channelId": channel_id,
            "creativeId": selection.creative.id,
            "advertiserId": selection.creative.advertiser_id,
        }

    async def _load_campaigns(self, ctx) -> dict[str, Campaign]:
        raw = await ctx.storage.get(CAMPAIGNS_KEY)
        if raw is None:
            return {}
        if not isinstance(raw, list):
            raise ValueError("Stored Awin campaigns are invalid.")
        values = [Campaign.from_dict(item) for item in raw]
        return {item.id: item for item in values}

    async def _save_campaigns(self, ctx, campaigns: Mapping[str, Campaign]) -> None:
        await ctx.storage.set(
            CAMPAIGNS_KEY,
            [campaign.to_dict() for campaign in sorted(campaigns.values(), key=lambda item: item.id)],
        )

    async def _schedule_campaign(self, ctx, campaign: Campaign) -> None:
        key = f"campaign:{campaign.id}"
        if not campaign.enabled:
            await ctx.scheduler.remove_job(key=key)
            return
        await ctx.scheduler.upsert_job(
            key=key,
            handler_id=CAMPAIGN_HANDLER_ID,
            schedule={"type": "interval", "seconds": campaign.interval_seconds},
            payload={"campaignId": campaign.id},
        )

    async def _run_campaign(self, ctx, campaign_id: str) -> Mapping[str, Any]:
        async with self._campaign_lock(ctx.guild_id, campaign_id):
            campaigns = await self._load_campaigns(ctx)
            campaign = campaigns.get(campaign_id)
            if campaign is None:
                raise ValueError("Campaign was not found.")

            selected, updated = choose_campaign_creative(campaign, await self.list_creatives(ctx))
            if selected is None:
                campaigns[campaign.id] = updated
                await self._save_campaigns(ctx, campaigns)
                history = append_history(
                    await ctx.storage.get(CAMPAIGN_HISTORY_KEY),
                    campaign_id=campaign.id,
                    outcome="blocked",
                    occurred_at=int(time.time()),
                    channel_id=campaign.channel_id,
                    reason=updated.blocked_reason or "no-creative",
                )
                await ctx.storage.set(CAMPAIGN_HISTORY_KEY, history)
                await ctx.audit.write(
                    action="awin.campaign-blocked",
                    target=campaign.id,
                    metadata={"reason": updated.blocked_reason or "no-creative"},
                )
                return {"sent": False, "blocked": True, "reason": updated.blocked_reason}

            rendered = render_post(selected)
            try:
                message_id = await ctx.discord.send_message(
                    channel_id=campaign.channel_id,
                    content=rendered["content"],
                    embed=rendered["embed"],
                    allowed_mentions=None,
                    link_buttons=rendered["linkButtons"],
                )
            except Exception:
                history = append_history(
                    await ctx.storage.get(CAMPAIGN_HISTORY_KEY),
                    campaign_id=campaign.id,
                    outcome="failed",
                    occurred_at=int(time.time()),
                    creative_id=selected.id,
                    channel_id=campaign.channel_id,
                    reason="discord-send-failed",
                )
                await ctx.storage.set(CAMPAIGN_HISTORY_KEY, history)
                raise
            campaigns[campaign.id] = updated
            await self._save_campaigns(ctx, campaigns)
            history = append_history(
                await ctx.storage.get(CAMPAIGN_HISTORY_KEY),
                campaign_id=campaign.id,
                outcome="sent",
                occurred_at=int(time.time()),
                creative_id=selected.id,
                channel_id=campaign.channel_id,
                message_id=message_id,
            )
            await ctx.storage.set(CAMPAIGN_HISTORY_KEY, history)

        await ctx.audit.write(
            action="awin.campaign-sent",
            target=campaign.id,
            metadata={
                "creativeId": selected.id,
                "channelId": campaign.channel_id,
                "messageId": message_id,
            },
        )
        return {
            "sent": True,
            "blocked": False,
            "messageId": message_id,
            "creativeId": selected.id,
            "campaignId": campaign.id,
        }

    async def _execute_campaign(self, ctx, job) -> None:
        campaign_id = str(job.payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("Scheduled Awin campaign payload is invalid.")
        campaigns = await self._load_campaigns(ctx)
        campaign = campaigns.get(campaign_id)
        if campaign is None or not campaign.enabled:
            return
        await self._run_campaign(ctx, campaign_id)

    async def _manage_campaign_list(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        campaigns = await self._load_campaigns(ctx)
        return {"campaigns": [item.to_dict() for item in sorted(campaigns.values(), key=lambda item: item.name.lower())]}

    async def _manage_campaign_create(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            channel_id = int(payload["channelId"])
            interval_seconds = int(payload["intervalSeconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("channelId and intervalSeconds are required.") from exc
        channel_id = await self._validated_post_channel(ctx, channel_id)
        selected = payload.get("selectedCreativeIds")
        if isinstance(selected, str):
            selected_ids = (selected,)
        elif isinstance(selected, list):
            selected_ids = tuple(str(item).strip() for item in selected if str(item).strip())
        else:
            selected_ids = ()
        campaign = Campaign(
            id=uuid.uuid4().hex,
            name=str(payload.get("name", "")).strip(),
            advertiser_id=str(payload.get("advertiserId", "")).strip(),
            channel_id=channel_id,
            selected_creative_ids=selected_ids,
            rotation=str(payload.get("rotation", "shuffle")).strip().lower(),
            interval_seconds=interval_seconds,
            enabled=bool(payload.get("enabled", True)),
            avoid_immediate_repeat=bool(payload.get("avoidImmediateRepeat", True)),
        )
        validate_campaign(campaign)
        known = {item.id: item for item in await self.list_creatives(ctx)}
        missing = [item for item in campaign.selected_creative_ids if item not in known]
        if missing:
            raise ValueError("Campaign contains unknown Creative IDs.")
        if any(known[item].advertiser_id != campaign.advertiser_id for item in campaign.selected_creative_ids):
            raise ValueError("Campaign Creatives must belong to the selected advertiser.")

        async with self._creative_lock(ctx.guild_id):
            campaigns = await self._load_campaigns(ctx)
            if len(campaigns) >= MAX_CAMPAIGNS:
                raise ValueError(f"At most {MAX_CAMPAIGNS} Awin campaigns can be configured.")
            campaigns[campaign.id] = campaign
            await self._save_campaigns(ctx, campaigns)
        await self._schedule_campaign(ctx, campaign)
        await ctx.audit.write(action="awin.campaign-created", target=campaign.id)
        return {"campaign": campaign.to_dict()}

    async def _manage_campaign_set_active(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        active = payload.get("active")
        if not campaign_id or not isinstance(active, bool):
            raise ValueError("campaignId and boolean active are required.")
        async with self._creative_lock(ctx.guild_id):
            campaigns = await self._load_campaigns(ctx)
            campaign = campaigns.get(campaign_id)
            if campaign is None:
                raise ValueError("Campaign was not found.")
            campaign = Campaign.from_dict({**campaign.to_dict(), "enabled": active, "blockedReason": None})
            campaigns[campaign_id] = campaign
            await self._save_campaigns(ctx, campaigns)
        await self._schedule_campaign(ctx, campaign)
        return {"campaign": campaign.to_dict()}

    async def _manage_campaign_delete(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("campaignId is required.")
        async with self._creative_lock(ctx.guild_id):
            campaigns = await self._load_campaigns(ctx)
            if campaign_id not in campaigns:
                raise ValueError("Campaign was not found.")
            campaigns.pop(campaign_id)
            await self._save_campaigns(ctx, campaigns)
        await ctx.scheduler.remove_job(key=f"campaign:{campaign_id}")
        await ctx.audit.write(action="awin.campaign-deleted", target=campaign_id)
        return {"deleted": True, "campaignId": campaign_id}

    async def _manage_campaign_run_now(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("campaignId is required.")
        return await self._run_campaign(ctx, campaign_id)

    async def _manage_campaign_get(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("campaignId is required.")
        campaigns = await self._load_campaigns(ctx)
        campaign = campaigns.get(campaign_id)
        if campaign is None:
            raise ValueError("Campaign was not found.")
        return {"campaign": campaign_status(campaign, await self.list_creatives(ctx))}

    async def _manage_campaign_update(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("campaignId is required.")
        async with self._campaign_lock(ctx.guild_id, campaign_id):
            campaigns = await self._load_campaigns(ctx)
            current = campaigns.get(campaign_id)
            if current is None:
                raise ValueError("Campaign was not found.")
            try:
                channel_id = int(payload.get("channelId", current.channel_id))
                interval_seconds = int(payload.get("intervalSeconds", current.interval_seconds))
            except (TypeError, ValueError) as exc:
                raise ValueError("channelId and intervalSeconds must be integers.") from exc
            channel_id = await self._validated_post_channel(ctx, channel_id)
            raw_selected = payload.get("selectedCreativeIds", list(current.selected_creative_ids))
            if isinstance(raw_selected, str):
                selected_ids = (raw_selected.strip(),) if raw_selected.strip() else ()
            elif isinstance(raw_selected, list):
                selected_ids = tuple(str(item).strip() for item in raw_selected if str(item).strip())
            else:
                raise ValueError("selectedCreativeIds must be a string or list.")
            advertiser_id = str(payload.get("advertiserId", current.advertiser_id)).strip()
            rotation = str(payload.get("rotation", current.rotation)).strip().lower()
            name = str(payload.get("name", current.name)).strip()
            avoid = payload.get("avoidImmediateRepeat", current.avoid_immediate_repeat)
            if not isinstance(avoid, bool):
                raise ValueError("avoidImmediateRepeat must be a boolean.")

            known = {item.id: item for item in await self.list_creatives(ctx)}
            if any(item not in known for item in selected_ids):
                raise ValueError("Campaign contains unknown Creative IDs.")
            if any(known[item].advertiser_id != advertiser_id for item in selected_ids):
                raise ValueError("Campaign Creatives must belong to the selected advertiser.")

            updated = update_campaign(
                current,
                name=name,
                advertiser_id=advertiser_id,
                channel_id=channel_id,
                selected_creative_ids=selected_ids,
                rotation=rotation,
                interval_seconds=interval_seconds,
                avoid_immediate_repeat=avoid,
            )
            campaigns[campaign_id] = updated
            await self._save_campaigns(ctx, campaigns)
        await self._schedule_campaign(ctx, updated)
        await ctx.audit.write(action="awin.campaign-updated", target=campaign_id)
        return {"campaign": campaign_status(updated, await self.list_creatives(ctx))}

    async def _manage_campaign_preview_next(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("campaignId is required.")
        campaigns = await self._load_campaigns(ctx)
        campaign = campaigns.get(campaign_id)
        if campaign is None:
            raise ValueError("Campaign was not found.")
        selected, preview_state = choose_campaign_creative(campaign, await self.list_creatives(ctx))
        if selected is None:
            return {
                "campaignId": campaign_id,
                "blocked": True,
                "reason": preview_state.blocked_reason,
                "preview": None,
            }
        return {
            "campaignId": campaign_id,
            "blocked": False,
            "preview": {
                "creativeId": selected.id,
                "advertiserId": selected.advertiser_id,
                **render_post(selected),
            },
            "rotationMutationApplied": False,
        }

    async def _manage_campaign_history(self, ctx, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("campaignId is required.")
        campaigns = await self._load_campaigns(ctx)
        if campaign_id not in campaigns:
            raise ValueError("Campaign was not found.")
        try:
            limit = int(payload.get("limit", 25))
        except (TypeError, ValueError) as exc:
            raise ValueError("limit must be an integer.") from exc
        rows = history_for_campaign(
            await ctx.storage.get(CAMPAIGN_HISTORY_KEY),
            campaign_id=campaign_id,
            limit=limit,
        )
        return {"campaignId": campaign_id, "history": rows}

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
