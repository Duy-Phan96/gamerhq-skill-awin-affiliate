# Architecture

## Boundary

Awin Affiliate is a standalone external Skill. It owns Awin-specific configuration, creative records, posting behavior, future campaign schedules, rotation and history.

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

A manual paste can be incomplete. Therefore an HTML import may add or refresh records, but it must never mark creatives missing merely because they were absent from that paste.

Missing-state transitions belong to authoritative full synchronization sources only.

## Authenticated Awin access

The public GamerHQ Skill Runtime now provides host-neutral external HTTP and encrypted Skill secret-storage ports. This Skill uses only those public contracts for Awin authentication and API calls; it never reads GamerHQ environment variables, databases or host internals.

## Storage

Current stable key:

- `creatives.v1`

Records use a normalized `Creative` model so future sources can converge on the same local library.


## Saved-page authority

A saved My Creative page can be partial because of filters or pagination. Therefore all saved-page groups are UPSERT_ONLY by default. The caller may explicitly mark one advertiser ID as complete; only that advertiser's snapshot becomes authoritative and may transition previously source-owned Creatives to MISSING.
