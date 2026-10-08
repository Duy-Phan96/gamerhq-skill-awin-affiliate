# Awin Affiliate 1.0 readiness audit

Audit baseline: Awin Affiliate 0.9.0 after adoption of the autonomous repository-ownership model.

## Repository ownership

This repository owns the portable `awin-affiliate` Skill package only.

No Host, web, Runtime/SDK or other Skill repository change is required by the findings below.

## Reviewed surfaces

- package and manifest version/identity
- public Management API inventory
- storage and secret keys
- Creative persistence
- campaign persistence and derived state
- posting preview/confirmation boundary
- scheduler ownership
- credential handling
- offline tests and release documentation

## Findings resolved in 0.9.1

### Strict campaign booleans

Campaign create previously used Python truthiness for `enabled` and `avoidImmediateRepeat`.

A string such as `"false"` could therefore become `True`.

0.9.1 requires actual boolean values and fails closed on other types.

### Strict persisted booleans

Stored Creative `userEnabled` and Campaign `enabled` / `avoidImmediateRepeat` fields previously used truthiness conversion.

0.9.1 rejects malformed persisted types instead of silently changing their meaning.

### Current blocked status

A Campaign can persist a blocked reason after a run with zero eligible Creatives.

If a Creative later becomes eligible again, management status must reflect current eligibility rather than stale persisted diagnostic state.

0.9.1 derives active/blocked status from current Creatives and suppresses stale blocked reasons in management responses.

### Campaign list/detail consistency

Campaign detail already exposed derived counts/status while campaign list returned raw persisted rows.

0.9.1 returns derived current status/count data from both list and detail contracts.

### Health consistency

Blocked campaign health counts now use the same current eligibility rule as Management APIs.

## Stable public identities

No storage key or Management contract ID changes were required.

Stable storage:

- `settings.v1`
- `creatives.v1`
- `post-state.v1`
- `campaigns.v1`
- `campaign-history.v1`

Stable secret key:

- `awin-access-token.v1`

Stable scheduler handler:

- `awin-affiliate.campaign.execute.v1`

Runtime API remains `1`.

## Security

No new capability is required.

The access token remains stored only through `secrets.skill`.

The hardening changes fail closed on malformed state and do not expose raw exception or credential material.

## Remaining Skill-owned work before 1.0

- final live provider acceptance using a dedicated test/non-production Awin credential where practical;
- confirm current public contracts/storage identities are the intended 1.0 compatibility baseline;
- decide whether the documented/safely testable Awin surface requires any additional authenticated Creative source.

Downstream Host rendering, package pinning and production deployment are not blockers owned by this repository.

If a missing public Runtime/SDK/Host capability is discovered during live acceptance, create a handoff rather than changing that repository from this project.
