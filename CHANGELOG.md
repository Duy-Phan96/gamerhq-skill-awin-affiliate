# Changelog

All notable changes to the standalone GamerHQ Awin Affiliate Skill are documented here.

The project follows semantic versioning while pre-1.0 contracts are still being hardened.

## [Unreleased]

### Remaining before 1.0

- GamerHQ host rendering for setup, Creative Library, Post Now and campaigns.
- Final live acceptance with a dedicated test Awin account / non-production credentials.
- Decide whether an authenticated Creative source is necessary if Awin exposes a supported/testable complete Creative Library surface.

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
- Added single, multi-select and advertiser-wide enable/disable controls.
- Added shared per-guild mutation locking for Creative state.

## [0.3.0]

- Added CreativeSource authority semantics.
- Added authoritative NEW / ACTIVE / MISSING / restored synchronization.
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
