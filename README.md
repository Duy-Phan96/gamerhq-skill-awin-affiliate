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
9. a shared Creative synchronization engine with explicit source authority,
10. safe NEW / ACTIVE / MISSING / restored transitions for authoritative sources,
11. bounded Creative Library pagination and filters,
12. Discord-native preview payloads,
13. single/multi-select and advertiser-wide enable/disable controls,
14. preview-confirmed Post Now with specific/random/next Creative selection,
15. Discord-native image embeds with a safe View offer link button,
16. mandatory visible affiliate disclosure on every sent post,
17. standalone recurring campaigns with fixed/sequential/random/shuffle rotation,
18. persisted scheduler jobs, pause/resume/delete and run-now controls,
19. campaign edit without changing stable campaign IDs,
20. non-mutating next-Creative preview and derived campaign status,
21. bounded recent campaign delivery history,
22. blocked-state handling when no eligible Creative remains,
23. offline tests with fake HTTP/secret/Discord/scheduler ports — no real Awin credentials required.

The Skill never imports GamerHQ host internals and remains usable without Recurring Posts.

## Roadmap

Next slices:

- authenticated Creative source adapter if required by Awin platform limitations
- host rendering for Creative Library controls
- host rendering for the full Post Now wizard
- host rendering for campaign management and diagnostics

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

Pre-1.0. Public contracts and storage keys should still be treated deliberately so migrations remain understandable.
