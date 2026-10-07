# Release readiness checklist

Use this checklist before promoting a reviewed Awin Affiliate Skill version.

## Package and contracts

- [ ] Skill ID remains `awin-affiliate`.
- [ ] Package entry point matches the Skill ID.
- [ ] Semantic package version matches `SkillManifest.version`.
- [ ] Runtime API compatibility is documented.
- [ ] Package capability metadata matches the executable manifest.
- [ ] Stable storage keys have not changed without a migration.
- [ ] Existing Management API meanings remain backward compatible or are versioned.

## Architecture

- [ ] No GamerHQ bot/cog/service/database/host imports.
- [ ] No Discord.py imports.
- [ ] No Recurring Posts dependency.
- [ ] Scheduling uses the public Runtime scheduler.
- [ ] Provider-specific ingestion remains behind CreativeSource boundaries.

## Security

- [ ] No real Awin token exists in source, tests, examples, screenshots or history.
- [ ] Token remains in encrypted Skill secret storage only.
- [ ] Diagnostics and health contain no credential material.
- [ ] Failure history contains generic codes, not raw exceptions.
- [ ] Saved HTML remains treated as untrusted input.
- [ ] Repository/history secret scan is clean where available.

## Functional tests

- [ ] Setup/token rejection.
- [ ] Publisher discovery/selection.
- [ ] Advertiser discovery.
- [ ] Manual HTML parsing.
- [ ] Saved-page multi-advertiser import.
- [ ] Authoritative missing/restored transitions.
- [ ] Creative enable/disable.
- [ ] Post preview/confirmation.
- [ ] Stale Creative revalidation.
- [ ] Campaign create/edit/pause/resume/delete.
- [ ] Fixed/sequential/random/shuffle rotation.
- [ ] Failed send does not advance rotation.
- [ ] Campaign history remains bounded.
- [ ] Secret-redaction diagnostics tests.

## CI

- [ ] Python 3.12 passes.
- [ ] Python 3.14 passes.
- [ ] Pinned reviewed GamerHQ Skill SDK commit is used.
- [ ] `pip check` passes.

## Downstream adoption checks

These checks are useful evidence for a Host that chooses to adopt this Skill, but they are **not release blockers for this repository**:

- external package is consumed from an immutable reviewed release/commit;
- setup, Creative Library, Post Now and campaign Management contracts can be rendered by that Host;
- live Discord acceptance uses non-production/test credentials where practical;
- affiliate disclosure is visible in the final rendered post;
- restart/recovery preserves Skill-owned campaign jobs.

A green Skill CI establishes this repository's release readiness only. Each downstream Host owns its own integration, release and deployment acceptance.
