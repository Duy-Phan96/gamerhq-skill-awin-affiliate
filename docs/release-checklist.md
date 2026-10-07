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

## Host acceptance before 1.0

- [ ] External Skill is pinned immutably by the GamerHQ host.
- [ ] Setup flow is usable through the host UI.
- [ ] Creative Library is usable through the host UI.
- [ ] Post Now preview/confirm is usable through the host UI.
- [ ] Campaign management/history is usable through the host UI.
- [ ] Live Discord smoke test uses non-production/test credentials where practical.
- [ ] Affiliate disclosure is visually visible in the final Discord post.
- [ ] Restart/recovery is verified with persisted campaign jobs.

A green Skill CI is necessary but does not replace host-level acceptance.
