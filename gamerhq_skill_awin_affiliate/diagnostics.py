from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from .campaigns import Campaign
from .models import Creative


def build_diagnostics(
    *,
    setup_status: Mapping[str, Any],
    creatives: Iterable[Creative],
    campaigns: Iterable[Campaign],
    history: Any,
) -> dict[str, Any]:
    creative_rows = list(creatives)
    campaign_rows = list(campaigns)
    history_rows = [item for item in history if isinstance(item, Mapping)] if isinstance(history, list) else []

    creative_states = Counter(item.state.value for item in creative_rows)
    enabled = sum(1 for item in creative_rows if item.user_enabled)
    disabled = len(creative_rows) - enabled

    campaign_states = Counter(
        "paused" if not item.enabled else "blocked" if item.blocked_reason else "active"
        for item in campaign_rows
    )
    outcomes = Counter(str(item.get("outcome", "unknown")) for item in history_rows)

    publisher = setup_status.get("publisher")
    safe_publisher = None
    if isinstance(publisher, Mapping):
        safe_publisher = {
            "id": str(publisher.get("id")) if publisher.get("id") is not None else None,
            "name": str(publisher.get("name")) if publisher.get("name") is not None else None,
        }

    return {
        "setup": {
            "connected": bool(setup_status.get("connected")),
            "publisherSelected": bool(setup_status.get("publisherSelected")),
            "publisher": safe_publisher,
            "tokenStored": bool(setup_status.get("connected")),
        },
        "creatives": {
            "total": len(creative_rows),
            "enabled": enabled,
            "disabled": disabled,
            "byState": dict(sorted(creative_states.items())),
        },
        "campaigns": {
            "total": len(campaign_rows),
            "active": campaign_states.get("active", 0),
            "paused": campaign_states.get("paused", 0),
            "blocked": campaign_states.get("blocked", 0),
        },
        "deliveryHistory": {
            "retained": len(history_rows),
            "sent": outcomes.get("sent", 0),
            "blocked": outcomes.get("blocked", 0),
            "failed": outcomes.get("failed", 0),
        },
    }
