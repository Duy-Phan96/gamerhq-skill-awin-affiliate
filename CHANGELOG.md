# Changelog

All notable changes to the standalone GamerHQ Awin Affiliate Skill are documented here.

The project follows semantic versioning while pre-1.0 contracts are still being hardened.

## [Unreleased]

### Added

- Added a complete host-neutral Management API contract reference with request fields, response shapes, side effects, validation behavior and compatibility notes for every manifest-declared contract.
- Added a regression test that keeps the documented Management contract inventory synchronized with the executable manifest.
- Added a redacted live-acceptance report template covering package identity, provider setup, Creative ingestion, Post Now, Campaigns, restart recovery, diagnostics and final 1.0 sign-off.
- Added a lean contributor guide with local setup, security rules, branch workflow, compatibility rules and Definition of Done.
- Added an independent Skill release process covering versioning, CI/artifacts, stable-release gates, tags, GitHub Releases, optional PyPI publication and rollback boundaries.
- Added Issue #23 to capture the owner decision for legal/license identity and the initial 1.0 distribution channel without guessing either choice.
- Added a repository-local release preflight that validates package/manifest identity, Runtime metadata, entry points, capabilities, README/changelog version state and Management contract documentation.
- Added regression tests proving version drift is rejected and stable 1.x candidates require an approved `LICENSE` file.

### Changed

- Expanded the live-acceptance runbook with evidence-handling rules, failure classification and explicit links to the Management contract candidate, release process and decision gates.
- Expanded the release checklist to include Python 3.13, built wheel/source distribution, concurrency/contract checks, live-acceptance evidence and owner publication decisions.
- Updated project status and README so the remaining 1.0 gates are explicit: live provider acceptance plus the owner license/distribution decision.
- Centralized the package-owned runtime version and aligned the base, hardened and exported Skill manifests.
- CI now runs the release preflight before building the wheel and verifies installed distribution metadata against the package version constant.

### Remaining Skill-owned work before 1.0

- Execute the documented live acceptance runbook with a dedicated test Awin account or non-production credentials where practical.
- Complete and approve the redacted live-acceptance report.
- Complete the final 1.0 compatibility baseline review after that acceptance passes.
- Resolve Issue #23 and add the approved legal/license identity before publishing stable release artifacts.

## [0.9.3]

- Added one per-guild campaign-store mutation boundary while retaining per-campaign execution locks, preventing lost campaign rotation and delivery-history updates across concurrent campaigns.
- Serialized Run Now/scheduled execution against pause, edit and delete for the same campaign so in-flight runs cannot resurrect or overwrite newer management state.
- Added best-effort persisted-state compensation when campaign scheduler mutations fail.
- Added deterministic concurrency regression tests for parallel campaign runs and run-versus-pause/update/delete behavior.
- Required HTTPS Awin tracking/image URLs at import time and rejected URL credentials.
- Added render-time HTTPS validation for persisted Creative URLs.
- Bounded imported fallback titles to Discord's embed-title limit.
- Expanded CI to Python 3.12, 3.13 and 3.14 and verified an installed built wheel outside the source tree.
- Added a verified project-status/roadmap document and documented the 0.9.3 data-integrity milestone.

## [0.9.2]

- Added a complete offline V1 management-flow acceptance test covering setup, advertiser discovery, Creative import, Post Now, campaigns, Skill reinstantiation and diagnostics through fake public Runtime ports.
- Fixed saved My Creative import results so `groups` remains the numeric group count and detailed per-group synchronization results are exposed separately as `groupResults`.
- Revalidated the current official Awin provider surface and retained saved/manual My Creative HTML as the safe V1 Creative-library path instead of introducing undocumented authenticated scraping.
- Added a repository-local live acceptance runbook for the final pre-1.0 provider validation.

## [0.9.1]

- Adopted autonomous repository ownership and handoff-based cross-project coordination.
- Clarified that downstream Host rendering/deployment is not a release blocker owned by this repository.
- Rejects non-boolean campaign create values such as the string `"false"` instead of coercing them to `True`.
- Rejects corrupted persisted Creative/Campaign boolean fields instead of silently coercing them.
- Campaign list/detail status is derived from current Creative eligibility so recovered Creatives no longer leave stale blocked state in management views.
- Added focused 1.0-readiness regression coverage for these cases.

## [0.9.0]

- Added saved My Creative HTML import.
- Supports multiple advertisers in one saved page.
- Saved-page imports are UPSERT_ONLY by default.
- One advertiser can be explicitly confirmed as a complete authoritative snapshot.
- Preserves image title/alt text and dimensions where available.
- Updated architecture documentation for the public HTTP and encrypted secret-store SDK ports.

## [0.8.0]

- Added safe aggregate diagnostics.
- Added richer health detail for blocked campaigns.
- Added explicit secret-redaction regression coverage.
- Diagnostics never exposes the Awin access token or raw failure details.

## [0.7.0]

- Added stable-ID campaign editing.
- Added non-mutating Preview Next.
- Added derived campaign status and bounded recent history.
- Added safe sent, blocked and failed delivery outcomes.

## [0.6.0]

- Added standalone recurring Awin campaigns.
- Added fixed, sequential, random and shuffle rotation.
- Added pause, resume, delete and Run Now.
- Campaign execution uses the public shared Runtime scheduler and does not depend on Recurring Posts.

## [0.5.0]

- Added preview-confirmed Post Now.
- Added specific, random and next Creative selection.
- Added Discord image embeds, visible affiliate disclosure and safe HTTPS View offer buttons.
- Confirmation revalidates the selected Creative before sending.

## [0.4.0]

- Added Creative Library filtering and pagination.
- Added Creative previews.
- Added single/multi-select and advertiser-wide enable/disable controls.
- Added shared per-guild mutation locking for Creative state.

## [0.3.0]

- Added CreativeSource authority semantics.
- Added authoritative NEW / ACTIVE / MISSING / restored transitions for authoritative sources.
- Added safe manual HTML integration through the shared sync engine.

## [0.2.0]

- Added secure Awin account connection.
- Added encrypted token storage through the public Skill secret port.
- Added publisher account discovery/selection.
- Added advertiser/programme discovery.

## [0.1.0]

- Added normalized Creative model.
- Added Awin HTML banner parsing.
- Added persistent Creative Library foundation.
- Added standalone package/contract tests.
