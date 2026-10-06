# GamerHQ Awin Affiliate Skill

Standalone Awin Affiliate Skill for GamerHQ-compatible hosts.

> Early development: the first vertical slice focuses on importing Awin banner HTML into a normalized Creative Library without requiring real credentials.

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

## Current vertical slice

The initial implementation covers:

1. parsing supported Awin HTML banner snippets,
2. validating Awin tracking/image URLs,
3. normalizing them into Creative records,
4. deduplicating imports,
5. persisting a per-guild Creative Library through Skill Storage,
6. exposing offline management APIs for import/list operations,
7. testing everything without Awin credentials or network access.

The authenticated Awin API connection is intentionally deferred until the GamerHQ public Skill SDK exposes host-neutral HTTP and secret-storage ports. The Skill must not bypass the SDK by importing GamerHQ internals.

## Roadmap

Next slices:

- public SDK HTTP + secret-storage integration
- Awin account connection and publisher selection
- advertiser discovery
- official API-backed CreativeSource where supported
- creative preview / enable-disable UI
- Discord-native affiliate posts
- standalone campaign scheduler and rotation
- post history and admin diagnostics

## Compliance

Affiliate posts will default to a visible disclosure such as:

`Werbung · Affiliate-Link`

Supporting copy such as `Mit Nutzung des Links unterstützt ihr den Server.` is additional context and does not replace the disclosure.

## Development

Python 3.12+.

Tests are offline and must never require real Awin credentials.

```bash
python -m pytest
```

## Status

Pre-1.0. Public contracts and storage keys should still be treated deliberately so migrations remain understandable.
