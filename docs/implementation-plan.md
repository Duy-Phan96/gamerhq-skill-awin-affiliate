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

- add or consume host-neutral external HTTP port
- add or consume dedicated secret-storage port
- connect with Awin access token without exposing it
- retrieve accessible publisher accounts
- select/verify publisher account
- connection test and masked status

## Slice 3 — Advertisers and authoritative sync

- retrieve publisher programmes/advertisers through supported Awin APIs
- add `CreativeSource` protocol
- determine whether the complete publisher Creative Library is available via an official API
- if not, design an isolated authenticated importer rather than spreading scraping logic
- implement authoritative sync transitions: new, updated, missing, restored

## Slice 4 — Creative Library management

Status: implemented as host-neutral management contracts in 0.3.0.

- advertiser filtering
- bounded pagination
- active/enabled/type filters
- Discord-native preview payload
- single and multi-select enable/disable
- advertiser-wide enable/disable
- per-guild mutation locking to avoid lost updates

Host-specific Discord/Web rendering remains a separate adapter concern.

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
