# Awin Affiliate live acceptance report

> Copy this template to `docs/live-acceptance-report.md` for one controlled acceptance run. Record only redacted outcomes and safe evidence references. Never include tokens, encryption keys, private `.env` values, database contents or raw private logs.

## 1. Run metadata

| Field | Value |
|---|---|
| Date | `YYYY-MM-DD` |
| Tester | `<name or GitHub handle>` |
| Skill version | `0.9.3` |
| Skill commit | `<immutable commit SHA>` |
| Runtime API | `1` |
| Compatible host/version | `<redacted version/commit>` |
| Discord environment | `<isolated test server/channel description>` |
| Awin account type | `<test / non-production / production-like; no IDs or token>` |
| Report status | `IN PROGRESS / PASS / FAIL / BLOCKED` |

## 2. Security preflight

- [ ] A dedicated test or non-production Awin token is used where practical.
- [ ] The token will not be pasted into this report, GitHub, chat, screenshots or logs.
- [ ] The host encryption key is configured and will not be recorded here.
- [ ] Testing uses an isolated Discord channel/server where practical.
- [ ] No production database copy is exposed.
- [ ] Screenshots and logs are reviewed for secrets before storage or sharing.

Safe notes:

```text
<redacted notes only>
```

## 3. Package identity

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

Expected:

- Skill ID: `awin-affiliate`
- version: `0.9.3`
- Runtime API: `1`

Observed:

```text
<safe version/identity result>
```

Evidence reference:

```text
<safe CI/run/screenshot reference; never a secret-bearing URL or log excerpt>
```

## 4. Awin connection and publisher selection

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

Checklist:

- [ ] valid token is verified before persistence;
- [ ] raw token is not returned or rendered;
- [ ] one publisher auto-selects, or multiple publishers require explicit selection;
- [ ] selected publisher survives restart;
- [ ] normal Skill storage contains no token material.

Observed safe outcome:

```text
<e.g. Connected successfully; one publisher auto-selected; no token echoed>
```

Failure category, when applicable:

`SKILL / HOST / PROVIDER / ENVIRONMENT / UNKNOWN`

## 5. Advertiser discovery

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

- [ ] joined advertisers load successfully;
- [ ] returned names/IDs correspond to the test account;
- [ ] unauthorized/provider failures are shown safely.

Observed safe outcome:

```text
<counts or redacted advertiser labels only>
```

## 6. Creative ingestion and authority

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

- [ ] a known Awin image Creative imports successfully;
- [ ] tracking and image URLs are HTTPS;
- [ ] stable publisher/advertiser/Creative IDs are normalized;
- [ ] duplicate HTML rows are deduplicated;
- [ ] saved-page import remains UPSERT_ONLY by default;
- [ ] `completeAdvertiserId` is used only after explicit completeness confirmation;
- [ ] authoritative missing detection affects only the confirmed advertiser scope.

Import path used:

`MANUAL SNIPPET / SAVED MY CREATIVE HTML`

Observed safe outcome:

```text
<aggregate counts only; no complete private HTML required>
```

## 7. Creative Library

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

- [ ] list and pagination work;
- [ ] detail/preview show the expected Creative;
- [ ] dimensions and state are sensible;
- [ ] disable removes the Creative from eligibility;
- [ ] enable restores eligibility for an ACTIVE/NEW Creative.

Observed safe outcome:

```text
<redacted Creative label and PASS/FAIL notes>
```

## 8. Post Now preview and confirmation

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

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
<message/channel outcome without private IDs if unnecessary>
```

## 9. Campaign lifecycle

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

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
<redacted campaign outcome>
```

## 10. Restart recovery

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

- [ ] publisher selection persists;
- [ ] Creative Library persists;
- [ ] Campaign configuration persists;
- [ ] enabled scheduler jobs recover;
- [ ] no duplicate campaign jobs appear;
- [ ] no duplicate send occurs solely because of restart.

Observed safe outcome:

```text
<restart result and safe job counts>
```

## 11. Diagnostics and health

**Status:** `PASS / FAIL / BLOCKED / NOT RUN`

- [ ] setup/Creative/Campaign/history aggregates are accurate;
- [ ] raw Awin token is absent;
- [ ] masked token marker is absent from diagnostics;
- [ ] Authorization headers are absent;
- [ ] raw provider/Discord exceptions are absent;
- [ ] health detail contains no credential material.

Observed safe outcome:

```text
<aggregate-only result>
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
<none, or a redacted repository-owned change with Issue reference>
```

Required handoff, if any:

```text
<none, or HANDOFF REQUIRED reference>
```

## 13. Failures and follow-up

| Step | Status | Category | Safe description | Issue/Handoff |
|---|---|---|---|---|
| `<step>` | `FAIL/BLOCKED` | `SKILL/HOST/PROVIDER/ENVIRONMENT` | `<redacted>` | `#...` |

Rules:

- Skill defect → create a repository Issue and add a regression test.
- Missing public Host/Runtime/SDK capability → create `HANDOFF REQUIRED`.
- Provider/account/environment problem → record it as such; do not disguise it as a Skill pass.

## 14. Final decision

Overall result:

```text
PASS / FAIL / BLOCKED
```

- [ ] all required runbook sections passed;
- [ ] no unresolved Skill-owned functional or security blocker;
- [ ] Management API compatibility candidate accepted;
- [ ] storage/secret/scheduler identities accepted;
- [ ] Issue #23 license/distribution decisions resolved;
- [ ] repository is ready for a separate `1.0.0` release PR.

Approved by:

```text
<owner/reviewer and date>
```

## 15. Release boundary

Passing this report authorizes preparation of the **Skill repository's** `1.0.0` release only.

It does not authorize, schedule or imply a GamerHQ Host or production-server deployment.

## 16. Machine-readable release attestation

Fill this block only after every required section passes and the report is approved. Stable `1.x` release preflight reads these exact keys from `docs/live-acceptance-report.md`.

```text
LIVE_ACCEPTANCE_STATUS=PASS
LIVE_ACCEPTANCE_APPROVED_BY=<real owner/reviewer identity>
LIVE_ACCEPTANCE_APPROVED_AT=YYYY-MM-DD
LIVE_ACCEPTANCE_REVIEWED_COMMIT=<lowercase 40-character immutable commit SHA>
```

Rules:

- keep `LIVE_ACCEPTANCE_STATUS=PASS` only for an actually passed and approved run;
- use a real approver identity, not a role or placeholder;
- use an ISO date in `YYYY-MM-DD` format;
- record the exact immutable Skill commit that was accepted;
- save the completed report as `docs/live-acceptance-report.md`;
- never include a token, encryption key, private environment value or raw private log.
