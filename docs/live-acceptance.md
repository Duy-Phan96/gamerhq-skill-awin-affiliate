# Awin Affiliate live acceptance

This is the final repository-local acceptance procedure before considering the Skill ready for 1.0.

It validates the Skill against a real Awin publisher account without changing another repository.

## Preconditions

- use a dedicated test/non-production Awin token where practical;
- use a GamerHQ-compatible host that already implements this Skill's public Runtime capabilities;
- keep the raw token out of screenshots, logs, issues and chat transcripts;
- do not paste production host secrets into this repository;
- use an isolated Discord test channel where practical.

## Acceptance scope

### 1. Package identity

Confirm the installed package reports:

- Skill ID: `awin-affiliate`
- package/manifest version: current reviewed version
- Runtime API: `1`

### 2. Awin connection

Connect an Awin access token through:

`awin-affiliate.setup.connect.v1`

Expected:

- valid token is verified against Awin before persistence;
- one publisher account auto-selects;
- multiple accounts require explicit selection;
- the response never returns the raw token;
- status only indicates that a token is stored.

### 3. Publisher selection

Use:

- `awin-affiliate.setup.accounts.v1`
- `awin-affiliate.setup.select-publisher.v1`
- `awin-affiliate.setup.status.v1`

Expected:

- only publisher accounts available to the connected Awin user can be selected;
- selected publisher ID/name survives restart;
- no credential material appears in normal storage.

### 4. Advertiser discovery

Use:

`awin-affiliate.advertisers.list.v1`

Verify at least the `joined` relationship.

Expected:

- known joined programmes are returned;
- advertiser IDs/names match the Awin account;
- safe failure is returned for unavailable/unauthorized provider responses.

### 5. Creative ingestion

Use one known Awin image banner.

Preferred V1 path:

- copy a supported banner HTML snippet from My Creative; or
- use a saved My Creative HTML page.

Expected:

- tracking/image URLs are recognized as Awin URLs;
- publisher/advertiser/creative IDs are normalized;
- duplicate stable IDs are deduplicated;
- saved-page imports remain UPSERT_ONLY by default.

### 6. Authoritative saved-page confirmation

Only if the supplied saved page is known to contain the complete Creative set for one advertiser, explicitly pass:

`completeAdvertiserId`

Expected:

- only that advertiser scope becomes authoritative;
- other advertiser groups remain UPSERT_ONLY;
- previously source-owned omitted Creatives can become MISSING only inside that confirmed scope.

Do not infer completeness from filters, page size or browser state.

### 7. Creative Library

Use:

- `awin-affiliate.creatives.list.v1`
- `awin-affiliate.creatives.get.v1`
- `awin-affiliate.creatives.preview.v1`
- `awin-affiliate.creatives.set-enabled.v1`

Expected:

- pagination/filtering is bounded;
- preview image/tracking target match the imported Creative;
- disable excludes the Creative from Post Now/campaign eligibility;
- enable restores eligibility when state is ACTIVE/NEW.

### 8. Post Now

Use:

`awin-affiliate.post.preview.v1`

Test:

- specific Creative
- next selection
- random selection

Expected:

- preview has no send side effect;
- visible disclosure is present;
- image and safe offer link are correct;
- returned `confirmPayload` identifies the exact previewed Creative.

Then pass that exact payload to:

`awin-affiliate.post.send.v1`

Expected:

- the Skill revalidates the Creative;
- stale/disabled/MISSING Creatives fail safely;
- successful send persists last-Creative state for next selection.

### 9. Campaigns

Create a short test campaign at or above the 15-minute minimum.

Use:

- `awin-affiliate.campaigns.create.v1`
- `awin-affiliate.campaigns.get.v1`
- `awin-affiliate.campaigns.preview-next.v1`
- `awin-affiliate.campaigns.run-now.v1`
- `awin-affiliate.campaigns.set-active.v1`
- `awin-affiliate.campaigns.history.v1`

Expected:

- campaign ID remains stable;
- Preview Next does not advance persisted rotation;
- successful Run Now advances rotation only after Discord send succeeds;
- pause removes/halts the scheduled job;
- resume restores scheduling;
- history records sent/blocked/failed outcomes with safe reason codes only.

### 10. Restart recovery

Restart only the isolated test host/runtime used for acceptance.

Expected:

- publisher selection persists;
- Creative Library persists;
- campaign configuration persists;
- enabled scheduler jobs are restored;
- restart creates no duplicate campaign/job state.

### 11. Diagnostics and health

Use:

`awin-affiliate.diagnostics.v1`

Expected:

- aggregate setup/Creative/campaign/history state is accurate;
- raw token is absent;
- masked token marker is absent from diagnostics;
- raw provider/Discord exceptions are absent.

## Pass criteria

The acceptance passes when all tested public contracts behave as documented and no real credential/private value appears in output, logs or persisted normal Skill storage.

## Failure handling

If failure is caused by this repository's code, fix it here with a regression test.

If failure requires a missing public Runtime/SDK/Host capability, stop and create a HANDOFF REQUIRED request. Do not modify that repository from this project.

## 1.0 decision

After this runbook passes and the final compatibility baseline is reviewed:

- confirm stable storage/secret keys;
- confirm stable Management contract IDs;
- confirm Runtime API compatibility;
- promote the package to 1.0.0 in this repository only.

A 1.0.0 Skill release does not imply or authorize a GamerHQ production deployment.


## Automated prerequisite

Before executing this live runbook, the repository's offline end-to-end acceptance test must pass:

```text
tests/test_v1_offline_acceptance_flow.py
```

That test validates the complete Skill-owned workflow using fake public ports. Live acceptance remains necessary for real Awin provider behavior and real downstream host/Discord integration.
