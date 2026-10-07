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

Status: implemented.

- host-neutral external HTTP port
- dedicated encrypted secret-storage port
- Awin access-token verification without exposing it
- publisher account discovery and selection
- masked connection status
- programme / advertiser discovery

## Slice 3 — Advertisers and authoritative sync

Status: domain sync engine implemented; live authoritative Creative source still pending.

- publisher programme / advertiser discovery through supported Awin APIs
- `CreativeSource` protocol and explicit source authority
- official documentation review found no publisher API endpoint for the complete My Creative banner library
- manual HTML source is explicitly `UPSERT_ONLY`
- authoritative snapshots support new, updated, missing and restored transitions
- missing detection is limited to records owned by the authoritative source
- future authenticated Creative importer remains isolated behind the source boundary

## Slice 4 — Creative Library management

Status: host-neutral management contracts implemented in 0.4.0.

- advertiser/type/active/enabled filters
- bounded pagination
- Discord-native preview payload
- single and multi-select enable/disable
- advertiser-wide enable/disable
- shared per-guild mutation lock with Creative sync
- host-specific Discord/Web rendering remains separate

## Slice 5 — Post now

Status: implemented as preview-confirmed management contracts in 0.5.0.

- specific, random and next Creative selection
- advertiser-scoped random/next selection
- text-channel validation
- Discord-native image embed
- safe HTTPS View offer link button
- visible affiliate disclosure and supporting text
- preview returns the exact Creative ID used by confirmation
- successful sends persist last Creative per advertiser for next rotation

## Slice 6 — Standalone campaigns

Status: core lifecycle implemented in 0.6.0; management/history extension implemented in 0.7.0.

- campaign model owned by this Skill
- shared Runtime scheduler jobs (no Recurring Posts dependency)
- fixed, sequential, random and shuffle rotation
- avoid-immediate-repeat for random/shuffle
- pause/resume/delete/run-now
- persisted campaign state and scheduler jobs survive restart
- blocked state when zero eligible Creatives remain
- rotation advances only after a successful Discord send
- stable-ID campaign edit
- non-mutating next-Creative preview
- derived active/paused/blocked status
- bounded recent sent/blocked/failed history

## Slice 7 — History, hardening and documentation

- minimal post history
- admin diagnostics
- permission model
- secret redaction tests
- failure-state UX
- complete README/setup/security docs

Awin Affiliate must continue to operate when Recurring Posts is not installed.
