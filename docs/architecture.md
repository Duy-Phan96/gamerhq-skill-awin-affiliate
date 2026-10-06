# Architecture

## Boundary

Awin Affiliate is a standalone external Skill. It owns Awin-specific configuration, creative records, posting behavior, future campaign schedules, rotation and history.

It must not import GamerHQ application internals and must not depend on Recurring Posts.

## CreativeSource

Creative ingestion is intentionally provider-adapter based.

Current source:

- `AwinHtmlCreativeSource` — offline fallback parser for Awin image-banner snippets.

Planned sources:

- official Awin API-backed source, where the publisher API exposes the needed creative data;
- authenticated importer only if the required publisher creative library cannot be retrieved through a supported API.

Parsing or scraping selectors must stay isolated inside an adapter.

## Manual HTML semantics

A manual paste can be incomplete. Therefore an HTML import may add or refresh records, but it must never mark creatives missing merely because they were absent from that paste.

Missing-state transitions belong to authoritative full synchronization sources only.

## SDK gap for authenticated Awin access

The current public GamerHQ Skill Runtime exposes a capability identifier for external HTTP access, but the SkillContext does not yet expose a host-neutral HTTP client port. It also does not expose a dedicated secret-storage port.

Until those contracts exist, this repository will not bypass the Skill boundary through GamerHQ internals. Token-backed API sync should be added after the public SDK can provide safe HTTP and secret handling.

## Storage

Current stable key:

- `creatives.v1`

Records use a normalized `Creative` model so future sources can converge on the same local library.
