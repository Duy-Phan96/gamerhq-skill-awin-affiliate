# Project status and roadmap

Last reviewed: 2026-10-12

Repository: `Duy-Phan96/gamerhq-skill-awin-affiliate`

## Executive status

Awin Affiliate is a feature-complete engineering beta approaching 1.0.

Current package version: `0.9.3`

Current release state:

```text
BLOCKED BY LIVE ACCEPTANCE
```

The primary V1 workflow is implemented:

```text
Connect Awin
→ select publisher
→ discover advertisers
→ import/manage Creatives
→ preview and send an affiliate post
→ create and operate recurring Awin campaigns
→ inspect history and diagnostics
```

The repository releases independently. A successful Skill release does not authorize or imply a downstream GamerHQ Host deployment.

## Product vision

Target users are Discord-community administrators with an Awin publisher account and developers of GamerHQ-compatible hosts.

The Skill provides one portable, provider-specific boundary for:

- secure Awin account setup;
- advertiser/programme discovery;
- Creative ingestion and lifecycle management;
- disclosure-aware Discord posting;
- standalone recurring campaigns;
- bounded delivery history and safe diagnostics.

The product should remain a small, reliable Awin integration rather than becoming a central affiliate-platform orchestrator.

## Verified implementation

Implemented and covered by repository tests:

- Awin token verification through the public external-HTTP port;
- encrypted token persistence through the public Skill secret port;
- publisher account discovery and selection;
- advertiser/programme discovery;
- manual and saved My Creative HTML ingestion;
- explicit UPSERT_ONLY versus AUTHORITATIVE source semantics;
- NEW / ACTIVE / MISSING / restored Creative transitions;
- Creative Library filtering, pagination, preview and enable/disable controls;
- preview-confirmed Post Now with specific, random and next selection;
- mandatory affiliate disclosure and safe link-button payloads;
- standalone campaign create, edit, pause, resume, delete and Run Now;
- fixed, sequential, random and shuffle rotation;
- Preview Next without persisted rotation mutation;
- bounded sent/blocked/failed campaign history;
- aggregate diagnostics without credential material;
- complete offline V1 management-flow acceptance using fake public Runtime ports;
- concurrency-safe aggregate Campaign/History mutations across parallel campaigns;
- same-campaign serialization across Run Now, scheduled execution, pause, edit and delete;
- HTTPS-only imported and rendered Creative URLs;
- Discord-safe imported fallback-title bounds;
- built-wheel verification on Python 3.12, 3.13 and 3.14.

## Architecture decisions already made

- Skill ID remains `awin-affiliate`.
- Runtime API remains `1` for the current compatibility baseline.
- The Skill imports no GamerHQ Host internals and no Discord.py.
- Awin campaigns do not depend on Recurring Posts.
- Scheduling uses the public Runtime scheduler.
- Credentials use `secrets.skill`, never ordinary Skill storage.
- Creative ingestion remains behind source adapters.
- Manual/saved-page imports are UPSERT_ONLY unless one advertiser is explicitly confirmed complete.
- No authenticated browser-session scraper or guessed private Awin endpoint is part of V1.
- Cross-repository requirements are handled by handoff, not by modifying another repository.

## Stable identities under review for 1.0

Storage keys:

- `settings.v1`
- `creatives.v1`
- `post-state.v1`
- `campaigns.v1`
- `campaign-history.v1`

Secret key:

- `awin-access-token.v1`

Scheduler handler:

- `awin-affiliate.campaign.execute.v1`

Public Management API IDs are documented in `docs/storage-and-contracts.md`.

## Resolved highest-risk finding

The project audit found that campaign configuration and delivery history were shared aggregate values, while different code paths used incompatible lock scopes. Parallel read-modify-write operations could overwrite rotation, pause/update/delete changes or history rows.

0.9.3 resolves this with:

- one execution lock per campaign;
- one aggregate campaign-store lock per guild;
- latest-state reload before committing rotation;
- same-campaign serialization for Run Now, scheduled execution and management mutations;
- scheduler-failure compensation;
- deterministic concurrency regression tests.

Tracked by Issue #19.

## Completed milestone

### Milestone — 0.9.3 Data Integrity & Release Hardening

Status: Completed

Delivered:

- consistent per-guild campaign-store mutation boundary;
- retained per-campaign execution serialization;
- concurrency regression tests for multiple campaigns;
- protection against run-versus-pause/update/delete lost updates;
- HTTPS-only outbound Creative URLs;
- Discord-safe fallback title limits;
- built-wheel and Python 3.12/3.13/3.14 compatibility checks;
- clear project-status, architecture and release documentation.

Verified acceptance:

- parallel campaign runs preserve both campaign state updates and history rows;
- failed sends do not advance rotation;
- Preview Next remains non-mutating;
- storage keys and public Management API IDs remain unchanged;
- CI passes on Python 3.12, 3.13 and 3.14;
- built wheel imports successfully outside the source tree.

## Current milestone

### Milestone — Live Provider Acceptance

Status: Ready to execute; requires a real test/non-production Awin account and an isolated compatible host.

Tracker: Issue #18

Objective: validate the reviewed Skill against real provider and Discord behavior.

Required evidence:

- real token verification and publisher selection;
- joined advertiser discovery;
- real My Creative HTML import;
- Creative preview and enable/disable;
- preview-confirmed Post Now;
- campaign create, Preview Next, Run Now, pause/resume and history;
- restart recovery without duplicated jobs;
- diagnostics free of credential material.

## Planned stable release

### Milestone — 1.0.0 Stable Public Contract

Status: Planned

Entry criteria:

- live acceptance complete;
- public Management API IDs accepted as the stable V1 baseline;
- storage, secret and scheduler identities accepted as the stable V1 baseline;
- release checklist complete;
- final package build and CI green.

Expected release outputs:

- package/manifest version `1.0.0`;
- final changelog entry;
- immutable Git tag;
- GitHub Release;
- installable release artifacts.

## Prioritized backlog

### P1

1. Execute Issue #18 live acceptance.
2. Freeze and document the final 1.0 request/response compatibility baseline.
3. Confirm the intended legal/license identity and distribution channel.
4. Prepare the 1.0.0 release PR, tag, notes and artifacts after acceptance passes.

### P2

5. Expand request/response examples for all public Management contracts.
6. Add a lean contributor guide after the stable release baseline is accepted.
7. Refactor the large Management orchestrator only after the 1.0 compatibility baseline is stable.

### Explicitly postponed

- product feeds;
- conversion/click analytics;
- AI-generated affiliate copy;
- additional affiliate networks;
- generic cross-Skill orchestration;
- monetization work before real adoption evidence.

## Decisions still required

- confirm the final legal/license identity before publishing 1.0 artifacts;
- decide whether `setup.status.v1` should retain the masked `token` field as part of the stable contract;
- choose the final distribution channel: GitHub Release only, or GitHub Release plus PyPI;
- after live acceptance, confirm whether any real Awin payload requires an additive compatibility adjustment.

## Definition of success

Awin Affiliate reaches 1.0 when the existing user workflow is demonstrably reliable, secure, documented and independently releasable—not when more features have been added.
