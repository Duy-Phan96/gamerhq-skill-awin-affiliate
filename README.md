# GamerHQ Awin Affiliate Skill

Standalone Awin Affiliate Skill for GamerHQ-compatible hosts.

> Early development: account setup and publisher discovery are now implemented on top of the Creative Library foundation.

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

## Current vertical slices

The implementation currently covers:

1. secure Awin user access-token connection through the public Skill Runtime,
2. automatic publisher-account discovery,
3. automatic publisher selection when exactly one account is available,
4. an explicit publisher-selection state when several accounts are available,
5. safe connection status that never returns the token,
6. parsing supported Awin HTML banner snippets,
7. validating and normalizing creatives,
8. deduplicated per-guild Creative Library persistence,
9. offline tests with fake HTTP and secret-store ports.

Awin access tokens are stored only through `secrets.skill`. They are not copied into ordinary Skill Storage, management responses, audit metadata or repository fixtures.

### Host prerequisite

A GamerHQ host must configure `GAMERHQ_SKILL_SECRET_KEY` to make the `secrets.skill` capability available. Generate and retain a stable Fernet key in private deployment configuration. Do not commit it.

The Skill also requires the host-provided `http.external` capability for Awin API calls.

## Roadmap

Next slices:

- advertiser discovery and synchronization
- official API-backed CreativeSource where supported
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


## Awin account setup

The backend setup flow uses the official Awin Accounts API:

1. provide an Awin user access token through the trusted management surface;
2. the Skill validates it against Awin;
3. publisher accounts accessible to that Awin user are discovered automatically;
4. a single publisher is selected automatically;
5. if multiple publisher accounts are available, the UI should ask the administrator to choose one;
6. only after successful validation is the token stored in encrypted Skill secret storage.

Disconnecting removes both the stored token and the local connection profile.

The current repository exposes this through versioned Management APIs. A Discord slash-command facade such as `/awin setup` should call these contracts rather than duplicate connection logic.
