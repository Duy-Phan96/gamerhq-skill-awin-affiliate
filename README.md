# GamerHQ Awin Affiliate Skill

Standalone Awin Affiliate Skill for GamerHQ-compatible hosts.

> Engineering beta: the Skill includes secure Awin account connection, Creative synchronization/library management, preview-confirmed posting, standalone recurring campaigns, bounded history and safe diagnostics.

## Goals

- discover and synchronize Awin advertisers and Creatives
- browse, preview, enable and disable Creatives
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
26. complete offline V1 acceptance through fake public Runtime ports,
27. concurrency-safe campaign and history persistence across parallel operations,
28. HTTPS-only outbound Creative URLs with render-time revalidation,
29. built-wheel verification on Python 3.12, 3.13 and 3.14.

The Skill never imports GamerHQ host internals and remains usable without Recurring Posts.

## Roadmap

The **0.9.3 Data Integrity & Release Hardening** milestone is complete.

The current Skill-owned gate is **Live Provider Acceptance**, tracked by Issue #18. It validates real Awin account responses, Creative ingestion, Discord posting, campaign operation and restart recovery. After that acceptance passes, the next planned milestone is **1.0.0 Stable Public Contract**.

Future provider capabilities remain optional and must belong to this Skill, use stable public contracts and be backed by a supported or safely testable Awin surface.

Downstream host rendering is not implemented from this repository. A GamerHQ-compatible host may independently consume the public Management contracts exposed by this Skill. Any missing Host/Runtime capability is handled through a handoff rather than cross-repository modification.

See [Project status and roadmap](docs/project-status.md) for the verified current state, priorities and release gates.

## Compliance

Affiliate posts default to a visible disclosure:

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

The access token is never returned after setup; status only exposes connection state and a compatibility-safe masked marker where applicable.

See `docs/awin-api.md` for API details and limitations.

## Development

Python 3.12+.

Tests are offline and must never require real Awin credentials.

```bash
python -m pytest
```

CI builds and installs the package wheel before running the suite on Python 3.12, 3.13 and 3.14.

## Status

Current package version: **0.9.3**

Current release state:

```text
BLOCKED BY LIVE ACCEPTANCE
```

This repository owns only the Awin Skill package. A green Skill release does not imply a GamerHQ production deployment or require a synchronized Host release. Public contracts and storage keys are treated as the intended 1.0 compatibility baseline pending the final live acceptance review.

## Saved My Creative HTML import

When the complete banner library is unavailable through a documented Publisher API, an administrator can save/export the rendered My Creative HTML and import it through the Skill.

The importer can discover multiple advertisers from Awin tracking links in one page. Imports are **UPSERT_ONLY by default**. Missing detection is enabled only when the administrator explicitly supplies one `completeAdvertiserId`, confirming that the saved HTML represents the complete Creative set for that advertiser. Other advertisers in the same page remain UPSERT_ONLY.

## Documentation

- [Project status and roadmap](docs/project-status.md)
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
