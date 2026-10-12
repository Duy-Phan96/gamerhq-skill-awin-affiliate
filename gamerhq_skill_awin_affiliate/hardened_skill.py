from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from .campaigns import (
    CAMPAIGNS_KEY,
    CAMPAIGN_HISTORY_KEY,
    MAX_CAMPAIGNS,
    Campaign,
    append_history,
    campaign_status,
    choose_campaign_creative,
    update_campaign,
    validate_campaign,
)
from .posting import render_post
from .skill import AwinAffiliateSkill as _BaseAwinAffiliateSkill


class AwinAffiliateSkill(_BaseAwinAffiliateSkill):
    """0.9.3 implementation with concurrency-safe campaign persistence.

    Each campaign retains its own execution lock so unrelated Discord sends may
    run concurrently. All aggregate campaign/history read-modify-write cycles
    additionally use one per-guild store lock, preventing lost updates across
    different campaigns.
    """

    manifest = replace(_BaseAwinAffiliateSkill.manifest, version="0.9.3")

    def __init__(self) -> None:
        super().__init__()
        self._campaign_store_locks: dict[int, asyncio.Lock] = {}

    def _campaign_store_lock(self, guild_id: int) -> asyncio.Lock:
        return self._campaign_store_locks.setdefault(guild_id, asyncio.Lock())

    async def _restore_campaign_after_scheduler_failure(
        self,
        ctx,
        *,
        campaign_id: str,
        restore: Campaign | None,
    ) -> None:
        """Best-effort compensation after a scheduler operation fails."""

        async with self._campaign_store_lock(ctx.guild_id):
            campaigns = await self._load_campaigns(ctx)
            if restore is None:
                campaigns.pop(campaign_id, None)
            else:
                campaigns[campaign_id] = restore
            await self._save_campaigns(ctx, campaigns)

        try:
            if restore is None:
                await ctx.scheduler.remove_job(key=f"campaign:{campaign_id}")
            else:
                await self._schedule_campaign(ctx, restore)
        except Exception:
            # Preserve the original scheduler error. A later management action
            # or host repair can reconcile the public scheduler state.
            pass

    async def _run_campaign(
        self,
        ctx,
        campaign_id: str,
        *,
        require_enabled: bool = False,
        missing_ok: bool = False,
    ) -> Mapping[str, Any]:
        async with self._campaign_lock(ctx.guild_id, campaign_id):
            async with self._campaign_store_lock(ctx.guild_id):
                campaigns = await self._load_campaigns(ctx)
                campaign = campaigns.get(campaign_id)
                if campaign is None:
                    if missing_ok:
                        return {
                            "sent": False,
                            "blocked": False,
                            "missing": True,
                            "campaignId": campaign_id,
                        }
                    raise ValueError("Campaign was not found.")
                if require_enabled and not campaign.enabled:
                    return {
                        "sent": False,
                        "blocked": False,
                        "inactive": True,
                        "campaignId": campaign_id,
                    }

                selected, updated = choose_campaign_creative(
                    campaign,
                    await self.list_creatives(ctx),
                )
                if selected is None:
                    latest = campaigns[campaign.id]
                    campaigns[campaign.id] = replace(
                        latest,
                        blocked_reason=updated.blocked_reason,
                    )
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

            if selected is None:
                await ctx.audit.write(
                    action="awin.campaign-blocked",
                    target=campaign.id,
                    metadata={"reason": updated.blocked_reason or "no-creative"},
                )
                return {
                    "sent": False,
                    "blocked": True,
                    "reason": updated.blocked_reason,
                }

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
                async with self._campaign_store_lock(ctx.guild_id):
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

            async with self._campaign_store_lock(ctx.guild_id):
                campaigns = await self._load_campaigns(ctx)
                current = campaigns.get(campaign.id)
                if current is None:
                    history = append_history(
                        await ctx.storage.get(CAMPAIGN_HISTORY_KEY),
                        campaign_id=campaign.id,
                        outcome="sent",
                        occurred_at=int(time.time()),
                        creative_id=selected.id,
                        channel_id=campaign.channel_id,
                        message_id=message_id,
                        reason="campaign-state-missing-after-send",
                    )
                    await ctx.storage.set(CAMPAIGN_HISTORY_KEY, history)
                    raise ValueError(
                        "Campaign state disappeared after the Discord post was sent."
                    )

                campaigns[campaign.id] = replace(
                    current,
                    last_creative_id=updated.last_creative_id,
                    sequential_index=updated.sequential_index,
                    shuffle_remaining=updated.shuffle_remaining,
                    blocked_reason=updated.blocked_reason,
                )
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
        await self._run_campaign(
            ctx,
            campaign_id,
            require_enabled=True,
            missing_ok=True,
        )

    async def _manage_campaign_create(
        self,
        ctx,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        try:
            channel_id = int(payload["channelId"])
            interval_seconds = int(payload["intervalSeconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("channelId and intervalSeconds are required.") from exc
        channel_id = await self._validated_post_channel(ctx, channel_id)

        selected = payload.get("selectedCreativeIds")
        if isinstance(selected, str):
            selected_ids = (selected.strip(),) if selected.strip() else ()
        elif isinstance(selected, list):
            selected_ids = tuple(
                str(item).strip() for item in selected if str(item).strip()
            )
        else:
            selected_ids = ()

        enabled = payload.get("enabled", True)
        avoid_immediate_repeat = payload.get("avoidImmediateRepeat", True)
        if not isinstance(enabled, bool) or not isinstance(
            avoid_immediate_repeat,
            bool,
        ):
            raise ValueError("enabled and avoidImmediateRepeat must be booleans.")

        campaign = Campaign(
            id=uuid.uuid4().hex,
            name=str(payload.get("name", "")).strip(),
            advertiser_id=str(payload.get("advertiserId", "")).strip(),
            channel_id=channel_id,
            selected_creative_ids=selected_ids,
            rotation=str(payload.get("rotation", "shuffle")).strip().lower(),
            interval_seconds=interval_seconds,
            enabled=enabled,
            avoid_immediate_repeat=avoid_immediate_repeat,
        )
        validate_campaign(campaign)

        known = {item.id: item for item in await self.list_creatives(ctx)}
        if any(item not in known for item in campaign.selected_creative_ids):
            raise ValueError("Campaign contains unknown Creative IDs.")
        if any(
            known[item].advertiser_id != campaign.advertiser_id
            for item in campaign.selected_creative_ids
        ):
            raise ValueError(
                "Campaign Creatives must belong to the selected advertiser."
            )

        async with self._campaign_lock(ctx.guild_id, campaign.id):
            async with self._campaign_store_lock(ctx.guild_id):
                campaigns = await self._load_campaigns(ctx)
                if len(campaigns) >= MAX_CAMPAIGNS:
                    raise ValueError(
                        f"At most {MAX_CAMPAIGNS} Awin campaigns can be configured."
                    )
                campaigns[campaign.id] = campaign
                await self._save_campaigns(ctx, campaigns)
            try:
                await self._schedule_campaign(ctx, campaign)
            except Exception:
                await self._restore_campaign_after_scheduler_failure(
                    ctx,
                    campaign_id=campaign.id,
                    restore=None,
                )
                raise

        await ctx.audit.write(action="awin.campaign-created", target=campaign.id)
        return {
            "campaign": campaign_status(campaign, await self.list_creatives(ctx))
        }

    async def _manage_campaign_set_active(
        self,
        ctx,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        active = payload.get("active")
        if not campaign_id or not isinstance(active, bool):
            raise ValueError("campaignId and boolean active are required.")

        async with self._campaign_lock(ctx.guild_id, campaign_id):
            async with self._campaign_store_lock(ctx.guild_id):
                campaigns = await self._load_campaigns(ctx)
                current = campaigns.get(campaign_id)
                if current is None:
                    raise ValueError("Campaign was not found.")
                updated = replace(current, enabled=active, blocked_reason=None)
                campaigns[campaign_id] = updated
                await self._save_campaigns(ctx, campaigns)
            try:
                await self._schedule_campaign(ctx, updated)
            except Exception:
                await self._restore_campaign_after_scheduler_failure(
                    ctx,
                    campaign_id=campaign_id,
                    restore=current,
                )
                raise

        return {
            "campaign": campaign_status(updated, await self.list_creatives(ctx))
        }

    async def _manage_campaign_delete(
        self,
        ctx,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("campaignId is required.")

        async with self._campaign_lock(ctx.guild_id, campaign_id):
            async with self._campaign_store_lock(ctx.guild_id):
                campaigns = await self._load_campaigns(ctx)
                current = campaigns.get(campaign_id)
                if current is None:
                    raise ValueError("Campaign was not found.")
                campaigns.pop(campaign_id)
                await self._save_campaigns(ctx, campaigns)
            try:
                await ctx.scheduler.remove_job(key=f"campaign:{campaign_id}")
            except Exception:
                await self._restore_campaign_after_scheduler_failure(
                    ctx,
                    campaign_id=campaign_id,
                    restore=current,
                )
                raise

        await ctx.audit.write(action="awin.campaign-deleted", target=campaign_id)
        return {"deleted": True, "campaignId": campaign_id}

    async def _manage_campaign_update(
        self,
        ctx,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        campaign_id = str(payload.get("campaignId", "")).strip()
        if not campaign_id:
            raise ValueError("campaignId is required.")

        async with self._campaign_lock(ctx.guild_id, campaign_id):
            async with self._campaign_store_lock(ctx.guild_id):
                campaigns = await self._load_campaigns(ctx)
                current = campaigns.get(campaign_id)
                if current is None:
                    raise ValueError("Campaign was not found.")

            try:
                channel_id = int(payload.get("channelId", current.channel_id))
                interval_seconds = int(
                    payload.get("intervalSeconds", current.interval_seconds)
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "channelId and intervalSeconds must be integers."
                ) from exc
            channel_id = await self._validated_post_channel(ctx, channel_id)

            raw_selected = payload.get(
                "selectedCreativeIds",
                list(current.selected_creative_ids),
            )
            if isinstance(raw_selected, str):
                selected_ids = (
                    (raw_selected.strip(),) if raw_selected.strip() else ()
                )
            elif isinstance(raw_selected, list):
                selected_ids = tuple(
                    str(item).strip()
                    for item in raw_selected
                    if str(item).strip()
                )
            else:
                raise ValueError("selectedCreativeIds must be a string or list.")

            advertiser_id = str(
                payload.get("advertiserId", current.advertiser_id)
            ).strip()
            rotation = str(payload.get("rotation", current.rotation)).strip().lower()
            name = str(payload.get("name", current.name)).strip()
            avoid = payload.get(
                "avoidImmediateRepeat",
                current.avoid_immediate_repeat,
            )
            if not isinstance(avoid, bool):
                raise ValueError("avoidImmediateRepeat must be a boolean.")

            known = {item.id: item for item in await self.list_creatives(ctx)}
            if any(item not in known for item in selected_ids):
                raise ValueError("Campaign contains unknown Creative IDs.")
            if any(
                known[item].advertiser_id != advertiser_id for item in selected_ids
            ):
                raise ValueError(
                    "Campaign Creatives must belong to the selected advertiser."
                )

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

            async with self._campaign_store_lock(ctx.guild_id):
                campaigns = await self._load_campaigns(ctx)
                if campaign_id not in campaigns:
                    raise ValueError("Campaign was not found.")
                campaigns[campaign_id] = updated
                await self._save_campaigns(ctx, campaigns)
            try:
                await self._schedule_campaign(ctx, updated)
            except Exception:
                await self._restore_campaign_after_scheduler_failure(
                    ctx,
                    campaign_id=campaign_id,
                    restore=current,
                )
                raise

        await ctx.audit.write(action="awin.campaign-updated", target=campaign_id)
        return {
            "campaign": campaign_status(updated, await self.list_creatives(ctx))
        }
