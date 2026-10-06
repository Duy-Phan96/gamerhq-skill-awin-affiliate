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

## Authenticated Awin access

Authenticated Awin calls use only public Skill Runtime ports:

- `ctx.http` through the `http.external` capability;
- `ctx.secrets` through the `secrets.skill` capability.

The access token is never persisted in `creatives.v1` or `connection.v1`. Normal Skill Storage contains only non-secret connection metadata.

The first official adapter uses Awin's Accounts endpoint to discover publisher accounts. Advertiser/programme discovery is the next provider slice.

The full publisher banner/creative-library source remains behind the CreativeSource boundary. If the official APIs do not expose the complete library, an authenticated importer can be added as a separate adapter without leaking scraping concerns into domain code.

## Storage

Current stable key:

- `creatives.v1`

Records use a normalized `Creative` model so future sources can converge on the same local library.
