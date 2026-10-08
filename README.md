# GamerHQ Awin Affiliate Skill

Standalone Awin Affiliate Skill for GamerHQ-compatible hosts.

> Early development: the Skill now includes secure Awin account connection, Creative synchronization/library management, preview-confirmed posting, and standalone recurring Awin campaigns.

## Goals

- discover and synchronize Awin advertisers and creatives
- browse, preview, enable and disable creatives
- post affiliate banners to Discord with visible disclosure
- run recurring Awin campaigns with built-in rotation
- remain fully usable without the Recurring Posts Skill

## Architecture

This repository is an independent GamerHQ Skill package. It may use public Skill Runtime / SDK contracts, but it must not import GamerHQ bot internals or depend on another optional Skill.

**Awin Affiliate does not require the Recurring Posts Skill.**

Shared runtime primitives such as storage and scheduling may be used internally without introducing a dependency on another Skill.

## Current implementation

The current implementation covers:

1. secure Awin token verification through the public Runtime HTTP port,
2. encrypted token persistence through the public Skill secret-store port,
3. automatic publisher account discovery,
4. automatic selection when only one publisher account exists,
5. explicit publisher selection when multiple accounts exist,
6. Awin programme / advertiser discovery,
7. parsing supported Awin HTML banner snippets,
8. normalizing and persisting a Creative Library,
9. importing multi-advertiser banners from saved My Creative HTML pages,
10. a shared Creative synchronization engine with explicit source authority,
11. safe NEW / ACTIVE / MISSING / restored transitions for authoritative sources,
12. bounded Creative Library pagination and filters,
13. Discord-native preview payloads,
14. single/multi-select and advertiser-wide enable/disable controls,
15. preview-confirmed Post Now with specific/random/next Creative selection,
16. Discord-native image embeds with a safe View offer link button,
17. mandatory visible affiliate disclosure on every sent post,
18. standalone recurring campaigns with fixed/sequential/random/shuffle rotation,
19. persisted scheduler jobs, pause/resume/delete and run-now controls,
20. campaign edit without changing stable campaign IDs,
21. non-mutating next-Creative preview and derived campaign status,
22. bounded recent campaign delivery history,
23. blocked-state handling when no eligible Creative remains,
24. safe aggregate diagnostics for setup, Creative states, campaign states and delivery outcomes,
25. richer health detail including blocked campaign count without exposing credentials,
26. offline tests with fake HTTP/secret/Discord/scheduler ports — no real Awin credentials required.

The Skill never imports GamerHQ host internals and remains usable without Recurring Posts.

## Roadmap

Next Skill-owned slices:

- optional authenticated Creative source adapter only if a documented/safely testable Awin surface becomes available
- additional provider-side capabilities only when they belong to this Skill and can be expressed through stable public contracts

Downstream host rendering is not implemented from this repository. A GamerHQ-compatible host may independently consume the public Management contracts exposed by this Skill. Any missing Host/Runtime capability is handled through a handoff rather than cross-repository modification.

## Compliance

Affiliate posts will default to a visible disclosure such as:

`Werbung · Affiliate-Link`

Supporting copy such as `Mit Nutzung des Links unterstützt ihr den Server.` is additional context and does not replace the disclosure.

## Setup flow

The intended administrator flow is:

```text
Connect Awin token
→ validate against Awin
→ discover publisher accounts
→ auto-select one account or ask the admin to choose
→ browse advertisers/programmes
```

The access token is never returned after setup; status only exposes a masked marker.

See `docs/awin-api.md` for API details and limitations.

## Development

Python 3.12+.

Tests are offline and must never require real Awin credentials.

```bash
python -m pytest
```

## Status

Pre-1.0 and independently releasable.

This repository owns only the Awin Skill package. A green Skill release does not imply a GamerHQ production deployment or require a synchronized Host release. Public contracts and storage keys should still be treated deliberately so migrations remain understandable.


## Saved My Creative HTML import

When the complete banner library is unavailable through a documented Publisher API, an administrator can save/export the rendered My Creative HTML and import it through the Skill.

The importer can discover multiple advertisers from Awin tracking links in one page. Imports are **UPSERT_ONLY by default**. Missing detection is enabled only when the administrator explicitly supplies one `completeAdvertiserId`, confirming that the saved HTML represents the complete Creative set for that advertiser. Other advertisers in the same page remain UPSERT_ONLY.


## Documentation

- [Setup](docs/setup.md)
- [Architecture](docs/architecture.md)
- [Awin API integration](docs/awin-api.md)
- [Affiliate disclosure & compliance](docs/compliance.md)
- [Storage & public contracts](docs/storage-and-contracts.md)
- [Implementation plan](docs/implementation-plan.md)
- [1.0 readiness audit](docs/v1-readiness-audit.md)
- [Live acceptance before 1.0](docs/live-acceptance.md)
- [Release checklist](docs/release-checklist.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)
