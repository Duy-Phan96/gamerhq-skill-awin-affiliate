# V1 implementation plan

The repository is intentionally developed as complete vertical slices.

## Slice 1 — Creative import foundation

Status: implemented on the initial feature branch.

- normalized Creative model
- isolated `AwinHtmlCreativeSource`
- multi-banner HTML parsing and validation
- deduplicated persistent Creative Library
- management APIs to import and list creatives
- offline tests and portable Skill contract checks
- no credentials and no network dependency

## Slice 2 — Public SDK prerequisites + Awin connection

Status: implemented in the account-setup feature branch; depends on the reviewed Runtime HTTP/secrets contracts.

- consume host-neutral external HTTP port
- consume dedicated secret-storage port
- connect with Awin access token without exposing it
- retrieve accessible publisher accounts
- auto-select one publisher or request a choice when several exist
- revalidate publisher access before selection
- connection test and masked status
- explicit disconnect that removes stored credentials

## Slice 3 — Advertisers and authoritative sync

Next.

- retrieve publisher programmes/advertisers through the supported Awin Programmes API
- add `CreativeSource` protocol
- determine whether the complete publisher Creative Library is available via an official API
- if not, design an isolated authenticated importer rather than spreading scraping logic
- implement authoritative sync transitions: new, updated, missing, restored

## Slice 4 — Discord Creative Library UX

- advertiser selector
- pagination and filters
- preview
- enable/disable and multi-select
- safe confirmation summaries

## Slice 5 — Post now

- Discord-native image embed
- tracking URL button or SDK-supported equivalent
- advertiser context
- default visible affiliate disclosure
- preview before publish

## Slice 6 — Standalone campaigns

- campaign model owned by this Skill
- scheduler jobs via public Runtime scheduler
- fixed, sequential, random and shuffle rotation
- avoid-immediate-repeat
- persistence and restart recovery
- blocked state for zero eligible creatives

## Slice 7 — History, hardening and documentation

- minimal post history
- admin diagnostics
- permission model
- secret redaction tests
- failure-state UX
- complete README/setup/security docs

Awin Affiliate must continue to operate when Recurring Posts is not installed.
