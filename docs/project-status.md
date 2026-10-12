# Project status and roadmap

Last reviewed: 2026-10-12

Repository: `Duy-Phan96/gamerhq-skill-awin-affiliate`

## Executive status

Awin Affiliate is a feature-complete engineering beta approaching 1.0.

Current package version: `0.9.3`

Current release state:

```text
BLOCKED BY LIVE ACCEPTANCE
AND MAIN BRANCH PROTECTION
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
- built-wheel verification on Python 3.12, 3.13 and 3.14;
- complete host-neutral request/response documentation for every manifest-declared Management API;
- exact post-merge `main` wheel/source-distribution verification with clean installs and checksums;
- structured bug/feature/PR templates and CODEOWNERS;
- approved MIT license and Duy Phan package-author identity;
- GitHub Release only as the approved initial stable distribution channel;
- lean contributor, live-acceptance evidence and independent release workflows.

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
- The current `setup.status.v1` candidate retains a masked `token` compatibility marker; hosts must use `connected` and must not display or persist that marker.
- The project uses the MIT License with `Copyright (c) 2026 Duy Phan`.
- The initial stable distribution is GitHub Release only; PyPI is deferred.
- A Skill release is independent and never authorizes a downstream Host deployment.

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

Public Management API IDs are inventoried in `docs/storage-and-contracts.md`.

The complete request/response compatibility candidate is documented in `docs/management-api-contracts.md`. A regression test verifies that every manifest-declared Management API appears exactly once in that document.

## Resolved highest-risk finding

The project audit found that campaign configuration and delivery history were shared aggregate values, while different code paths used incompatible lock scopes. Parallel read-modify-write operations could overwrite rotation, pause/update/delete changes or history rows.

0.9.3 resolves this with:

- one execution lock per campaign;
- one aggregate campaign-store lock per guild;
- latest-state reload before committing rotation;
- same-campaign serialization for Run Now, scheduled execution and management mutations;
- scheduler-failure compensation;
- deterministic concurrency regression tests.

Tracked by completed Issue #19.

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
- exact-main wheel/source-distribution dry-run evidence;
- clear project-status, architecture and release documentation.

Verified acceptance:

- parallel campaign runs preserve both campaign state updates and history rows;
- failed sends do not advance rotation;
- Preview Next remains non-mutating;
- storage keys and public Management API IDs remain unchanged;
- CI passes on Python 3.12, 3.13 and 3.14;
- built wheel imports successfully outside the source tree;
- wheel and source distribution clean-install successfully from the exact reviewed `main` commit.

## Current milestone

### Milestone — Live Provider Acceptance

Status: Ready to execute; requires a real test/non-production Awin account and an isolated compatible host.

Tracker: Issue #18

Runbook:

- `docs/live-acceptance.md`

Evidence template:

- `docs/live-acceptance-report-template.md`

Objective: validate the reviewed Skill against real provider and Discord behavior while preserving a redacted, reproducible acceptance record.

Required evidence:

- real token verification and publisher selection;
- joined advertiser discovery;
- real My Creative HTML import;
- Creative preview and enable/disable;
- preview-confirmed Post Now;
- campaign create, Preview Next, Run Now, pause/resume and history;
- restart recovery without duplicated jobs or sends;
- diagnostics free of credential material;
- confirmation that real provider responses fit the documented compatibility candidate or require only an explicit additive adjustment.

## Completed owner decision

### Decision — License identity and distribution channel

Status: Completed

Tracker: Issue #23

Approved baseline:

```text
License: MIT
Copyright holder: Duy Phan
Package author: Duy Phan
Initial distribution: GitHub Release only
PyPI: deferred
```

The authoritative decision record is `docs/legal-and-distribution.md` and the approved legal text is the root `LICENSE` file.

### Decision — Main branch protection

Status: Open owner action

Tracker: Issue #33

Recommended before the final 1.0 release PR:

- require pull requests for `main`;
- require `test (3.12)`, `test (3.13)`, `test (3.14)` and the release artifact `build-and-verify` check where applicable;
- block force pushes and deletion of `main`;
- keep the process lightweight for a solo maintainer.

The connected repository automation cannot safely change repository-administration rules. The owner must enable the rule or record an explicit temporary exception before the final 1.0 release PR.

## Planned stable release

### Milestone — 1.0.0 Stable Public Contract

Status: Planned

Entry criteria:

- live acceptance report is `PASS`;
- the documented Management API compatibility candidate is accepted as the stable V1 baseline;
- storage, secret and scheduler identities are accepted as the stable V1 baseline;
- approved MIT/Duy Phan/GitHub Release only baseline remains implemented;
- Issue #33 branch protection is enabled or an explicit temporary owner exception is recorded;
- release checklist is complete;
- final package build and CI are green;
- exact post-merge `main` artifact dry run is green for the release commit.

Expected release outputs:

- package/manifest version `1.0.0`;
- final changelog entry;
- approved MIT `LICENSE` file;
- immutable Git tag;
- GitHub Release;
- installable wheel and source distribution;
- SHA-256 checksums;
- release notes with explicit downstream deployment boundary.

Release procedure:

- `docs/release-process.md`

## Prioritized backlog

### P1

1. Execute Issue #18 live acceptance and complete the report template.
2. Confirm or explicitly amend the documented 1.0 Management API baseline using live evidence.
3. Resolve Issue #33 by enabling branch protection or recording an explicit temporary owner exception.
4. Prepare the 1.0.0 release PR, tag, notes and GitHub Release artifacts after all entry gates pass.

### P2

5. Refactor the large Management orchestrator only after the 1.0 compatibility baseline is stable.
6. Add further provider capabilities only after real adoption evidence and a supported Awin surface exist.

### Completed repository-governance work

- `CONTRIBUTING.md` defines local setup, security, PR workflow and Definition of Done.
- issue and pull-request templates require evidence, impact analysis and repository-boundary checks.
- `CODEOWNERS` identifies repository review ownership.
- `docs/legal-and-distribution.md` records the approved legal identity and first stable channel.
- `docs/release-process.md` defines independent versioning, exact-main artifact evidence, tag, release and rollback behavior.
- `docs/live-acceptance-report-template.md` defines safe, redacted evidence capture.

### Explicitly postponed

- PyPI publication;
- product feeds;
- conversion/click analytics;
- AI-generated affiliate copy;
- additional affiliate networks;
- generic cross-Skill orchestration;
- monetization work before real adoption evidence.
