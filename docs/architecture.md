# Architecture

## Boundary

Awin Affiliate is a standalone external Skill. It owns Awin-specific configuration, Creative records, posting behavior, campaign schedules, rotation and history.

It must not import GamerHQ application internals and must not depend on Recurring Posts.

## CreativeSource

Creative ingestion is intentionally provider-adapter based.

Current sources:

- `AwinHtmlCreativeSource` — offline fallback parser for Awin image-banner snippets;
- `AwinSavedPageCreativeSource` — offline parser for saved My Creative HTML pages, grouped by publisher + advertiser.

Planned source:

- authenticated importer only if the complete publisher Creative Library becomes available through a supported or safely testable Awin surface.

Parsing or scraping selectors must stay isolated inside an adapter.

## Manual HTML semantics

A manual paste can be incomplete. Therefore an HTML import may add or refresh records, but it must never mark Creatives missing merely because they were absent from that paste.

Missing-state transitions belong to authoritative full synchronization sources only.

## Outbound URL boundary

Imported Awin tracking and image URLs must use HTTPS and must not contain URL credentials.

Posting validates HTTPS again at render time so malformed or legacy persisted values fail closed before a Discord payload is sent.

Imported fallback titles are bounded to Discord's embed-title limit. Explicit administrator titles continue to fail validation when they exceed the public limit rather than being silently shortened.

## Authenticated Awin access

The public GamerHQ Skill Runtime provides host-neutral external HTTP and encrypted Skill secret-storage ports. This Skill uses only those public contracts for Awin authentication and API calls; it never reads GamerHQ environment variables, databases or host internals.

## Storage

Stable storage keys:

- `settings.v1`
- `creatives.v1`
- `post-state.v1`
- `campaigns.v1`
- `campaign-history.v1`

Records use normalized domain models so future sources and host renderers can converge on the same public behavior.

## Campaign consistency

Campaign configuration is persisted as one aggregate value per guild under `campaigns.v1`. Campaign delivery history is persisted as one bounded aggregate value under `campaign-history.v1`.

The 0.9.3 concurrency model uses two lock levels:

1. **Per-campaign execution lock** — serializes Run Now, scheduled execution, pause/resume, edit and delete for the same campaign. The lock remains held across the Discord send so a management mutation cannot be overwritten by an in-flight run.
2. **Per-guild campaign-store lock** — protects every aggregate campaign/history read-modify-write cycle. Different campaigns may still send concurrently, but their commits are serialized and always reload the latest aggregate state before applying one campaign's update.

Lock order is always:

```text
per-campaign execution lock
→ per-guild campaign-store lock
```

This prevents lost updates without globally serializing unrelated network sends.

Scheduler changes occur while the per-campaign lock is held. If a scheduler mutation fails after storage changed, the Skill performs best-effort compensation to restore the previous persisted campaign state.

The public storage port does not currently provide a transaction spanning campaign state and history. The Skill therefore prioritizes persisting rotation state after a successful send before appending history, reducing duplicate-selection risk if the second write fails.

## Saved-page authority

A saved My Creative page can be partial because of filters or pagination. Therefore all saved-page groups are UPSERT_ONLY by default. The caller may explicitly mark one advertiser ID as complete; only that advertiser's snapshot becomes authoritative and may transition previously source-owned Creatives to MISSING.
