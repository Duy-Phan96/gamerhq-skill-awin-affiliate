# Awin Affiliate live acceptance report

> Current controlled acceptance record for the reviewed 0.9.3 baseline. Record only redacted outcomes and safe evidence references. Never include tokens, encryption keys, private `.env` values, database contents or raw private logs.

## 1. Run metadata

| Field | Value |
|---|---|
| Date | `2026-10-14` |
| Tester | `Duy Phan` |
| Skill version | `0.9.3` |
| Skill commit | `efdfc37256f69b1f868e6355c0d7906e0f85d078` |
| Runtime API | `1` |
| Compatible host/version | `TO BE RECORDED DURING LIVE RUN` |
| Discord environment | `TO BE RECORDED — isolated test server/channel` |
| Awin account type | `TO BE RECORDED — test/non-production preferred; no IDs or token` |
| Report status | `IN PROGRESS` |

### Automated baseline evidence

- Post-merge Skill CI run: `38552179168` — Python 3.12 / 3.13 / 3.14 PASS
- Exact-main artifact run: `38552179150` — PASS
- Release preflight: PASS
- Wheel and source distribution build: PASS
- Clean wheel install: PASS
- Clean source-distribution install: PASS
- Temporary artifact: `awin-affiliate-release-dry-run-efdfc37256f69b1f868e6355c0d7906e0f85d078`
- Artifact digest: `sha256:de0cd39d3509d2fe970cf2df5f06a0176ce82f8a95e652ab603c1e9dec02c9a7`
- Stable-release live-acceptance attestation gate: implemented and verified
- License: MIT
- Copyright holder/package author: Duy Phan
- Initial distribution: GitHub Release only; PyPI deferred

## 2. Security preflight

- [ ] A dedicated test or non-production Awin token is used where practical.
- [ ] The token will not be pasted into this report, GitHub, chat, screenshots or logs.
- [ ] The host encryption key is configured and will not be recorded here.
- [ ] Testing uses an isolated Discord channel/server where practical.
- [ ] No production database copy is exposed.
- [ ] Screenshots and logs are reviewed for secrets before storage or sharing.

Safe notes:

```text
NOT RUN
```

## 3. Package identity

**Status:** `NOT RUN`

Expected:

- Skill ID: `awin-affiliate`
- version: `0.9.3`
- Runtime API: `1`
- reviewed commit: `efdfc37256f69b1f868e6355c0d7906e0f85d078`

Observed:

```text
NOT RUN
```

Evidence reference:

```text
Automated repository baseline is recorded above. Live host identity still needs verification.
```

## 4. Awin connection and publisher selection

**Status:** `NOT RUN`

Checklist:

- [ ] valid token is verified before persistence;
- [ ] raw token is not returned or rendered;
- [ ] one publisher auto-selects, or multiple publishers require explicit selection;
- [ ] selected publisher survives restart;
- [ ] normal Skill storage contains no token material.

Observed safe outcome:

```text
NOT RUN
```

Failure category, when applicable:

`SKILL / HOST / PROVIDER / ENVIRONMENT / UNKNOWN`

## 5. Advertiser discovery

**Status:** `NOT RUN`

- [ ] joined advertisers load successfully;
- [ ] returned names/IDs correspond to the test account;
- [ ] unauthorized/provider failures are shown safely.

Observed safe outcome:

```text
NOT RUN
```

## 6. Creative ingestion and authority

**Status:** `NOT RUN`

- [ ] a known Awin image Creative imports successfully;
- [ ] tracking and image URLs are HTTPS;
- [ ] stable publisher/advertiser/Creative IDs are normalized;
- [ ] duplicate HTML rows are deduplicated;
- [ ] saved-page import remains UPSERT_ONLY by default;
- [ ] `completeAdvertiserId` is used only after explicit completeness confirmation;
- [ ] authoritative missing detection affects only the confirmed advertiser scope.

Import path used:

`NOT SELECTED`

Observed safe outcome:

```text
NOT RUN
```

## 7. Creative Library

**Status:** `NOT RUN`

- [ ] list and pagination work;
- [ ] detail/preview show the expected Creative;
- [ ] dimensions and state are sensible;
- [ ] disable removes the Creative from eligibility;
- [ ] enable restores eligibility for an ACTIVE/NEW Creative.

Observed safe outcome:

```text
NOT RUN
```

## 8. Post Now preview and confirmation

**Status:** `NOT RUN`

Selection modes tested:

- [ ] specific
- [ ] next
- [ ] random

Checklist:

- [ ] preview has no send side effect;
- [ ] disclosure is visible;
- [ ] image renders correctly;
- [ ] View offer uses a safe HTTPS URL;
- [ ] host forwards the returned `confirmPayload` unchanged;
- [ ] confirmation sends the exact previewed Creative;
- [ ] stale/disabled/MISSING Creative fails safely.

Observed safe outcome:

```text
NOT RUN
```

## 9. Campaign lifecycle

**Status:** `NOT RUN`

- [ ] campaign creation succeeds at an interval of at least 15 minutes;
- [ ] Preview Next does not advance persisted rotation;
- [ ] Run Now sends successfully;
- [ ] successful send advances rotation only after Discord success;
- [ ] failed send does not advance rotation;
- [ ] pause removes or halts recurring scheduling;
- [ ] resume restores scheduling;
- [ ] edit keeps the stable campaign ID;
- [ ] history records sent/blocked/failed with safe reason codes;
- [ ] delete removes campaign configuration and scheduler job.

Rotation modes sampled:

- [ ] fixed
- [ ] sequential
- [ ] random
- [ ] shuffle

Observed safe outcome:

```text
NOT RUN
```

## 10. Restart recovery

**Status:** `NOT RUN`

- [ ] publisher selection persists;
- [ ] Creative Library persists;
- [ ] Campaign configuration persists;
- [ ] enabled scheduler jobs recover;
- [ ] no duplicate campaign jobs appear;
- [ ] no duplicate send occurs solely because of restart.

Observed safe outcome:

```text
NOT RUN
```

## 11. Diagnostics and health

**Status:** `NOT RUN`

- [ ] setup/Creative/Campaign/history aggregates are accurate;
- [ ] raw Awin token is absent;
- [ ] masked token marker is absent from diagnostics;
- [ ] Authorization headers are absent;
- [ ] raw provider/Discord exceptions are absent;
- [ ] health detail contains no credential material.

Observed safe outcome:

```text
NOT RUN
```

## 12. Compatibility review

Documented compatibility candidate:

`docs/management-api-contracts.md`

- [ ] real Awin payloads fit the documented request/response assumptions;
- [ ] no existing `.v1` contract requires an incompatible change;
- [ ] storage identities are accepted for 1.0;
- [ ] secret key identity is accepted for 1.0;
- [ ] scheduler handler/job identity is accepted for 1.0.

Required additive adjustment, if any:

```text
NOT ASSESSED
```

Required handoff, if any:

```text
NONE IDENTIFIED BEFORE LIVE RUN
```

## 13. Failures and follow-up

| Step | Status | Category | Safe description | Issue/Handoff |
|---|---|---|---|---|
| Live acceptance | `NOT RUN` | `ENVIRONMENT` | Real Awin account and isolated compatible host are still required. | `#18` |

Rules:

- Skill defect → create a repository Issue and add a regression test.
- Missing public Host/Runtime/SDK capability → create `HANDOFF REQUIRED`.
- Provider/account/environment problem → record it as such; do not disguise it as a Skill pass.

## 14. Final decision

Overall result:

```text
IN PROGRESS
```

- [ ] all required runbook sections passed;
- [ ] no unresolved Skill-owned functional or security blocker;
- [ ] Management API compatibility candidate accepted;
- [ ] storage/secret/scheduler identities accepted;
- [x] Issue #23 license/distribution decisions resolved;
- [ ] Issue #33 branch protection enabled or explicit temporary owner exception recorded;
- [ ] repository is ready for a separate `1.0.0` release PR.

Approved by:

```text
PENDING
```

## 15. Release boundary

Passing this report authorizes preparation of the **Skill repository's** `1.0.0` release only.

It does not authorize, schedule or imply a GamerHQ Host or production-server deployment.

## 16. Machine-readable release attestation

This block is intentionally non-passing while the live run is incomplete. Replace all pending values only after every required section passes and the report is approved.

```text
LIVE_ACCEPTANCE_STATUS=IN_PROGRESS
LIVE_ACCEPTANCE_APPROVED_BY=PENDING
LIVE_ACCEPTANCE_APPROVED_AT=PENDING
LIVE_ACCEPTANCE_REVIEWED_COMMIT=efdfc37256f69b1f868e6355c0d7906e0f85d078
```

The stable `1.x` release preflight must continue to reject this report until:

- `LIVE_ACCEPTANCE_STATUS=PASS`;
- a real approver identity is recorded;
- an ISO approval date is recorded;
- the reviewed immutable commit matches the actually accepted Skill build.
