# Project status and roadmap

Last reviewed: 2026-10-12

Repository: `Duy-Phan96/gamerhq-skill-awin-affiliate`

## Executive status

Awin Affiliate is a feature-complete engineering beta approaching 1.0.

Current package version: `0.9.2`

Current release state:

```text
BLOCKED BY 0.9.3 DATA-INTEGRITY HARDENING
THEN BLOCKED BY LIVE ACCEPTANCE
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
- complete offline V1 management-flow acceptance using fake public Runtime ports.

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

## Current highest-risk finding

Campaign configuration and delivery history are aggregate values shared by all campaigns in one guild.

The pre-0.9.3 implementation uses different lock scopes for campaign execution and campaign-management mutations. Concurrent read-modify-write operations can therefore overwrite newer campaign rotation, pause/update/delete changes or history rows.

This is a data-integrity and 1.0 release blocker tracked by Issue #19.

## Current milestone

### Milestone — 0.9.3 Data Integrity & Release Hardening

Status: In Progress

Objective: make the existing V1 workflow reliable and formally release-ready without adding new product features.

Committed deliverables:

- consistent per-guild campaign-store mutation boundary;
- retained per-campaign execution serialization;
- concurrency regression tests for multiple campaigns;
- protection against run-versus-pause/update/delete lost updates;
- HTTPS-only outbound Creative URLs;
- Discord-safe fallback title limits;
- release-artifact and compatibility checks where repository-owned;
- clear project-status and public-contract documentation.

Acceptance criteria:

- no lost campaign-state or history updates under tested concurrency;
- failed sends do not advance rotation;
- Preview Next remains non-mutating;
- existing storage keys and Management API IDs remain stable;
- Python 3.12 and 3.14 CI pass;
- no unresolved P0/P1 Skill-owned blocker remains before live acceptance.

## Next milestone

### Milestone — Live Provider Acceptance

Status: Blocked by 0.9.3

Tracker: Issue #18

Objective: validate the reviewed Skill against a real test/non-production Awin publisher account and an isolated compatible host.

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

- 0.9.3 data-integrity hardening complete;
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

### P0

1. Prevent campaign and history lost updates under concurrent operations.

### P1

2. Enforce HTTPS-only imported tracking/image URLs and validate again before rendering/sending.
3. Bound imported fallback titles to Discord embed limits.
4. Complete release-artifact and compatibility CI hardening.
5. Execute Issue #18 live acceptance.

### P2

6. Expand request/response examples for all public Management contracts.
7. Add a lean contributor guide and repository license file after the owner confirms the intended legal identity.
8. Refactor the large Management orchestrator only after the 1.0 compatibility baseline is stable.

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
