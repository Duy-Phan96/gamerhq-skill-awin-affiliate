# Release readiness checklist

Use this checklist before promoting a reviewed Awin Affiliate Skill version.

The detailed workflow is in `docs/release-process.md`.

## Package and contracts

- [ ] Skill ID remains `awin-affiliate`.
- [ ] Package entry point matches the Skill ID.
- [ ] Semantic package version matches `SkillManifest.version`.
- [ ] Runtime API compatibility is documented.
- [ ] Package capability metadata matches the executable manifest.
- [ ] Stable storage keys have not changed without a migration.
- [ ] Secret and scheduler-handler identities have not changed without an explicit compatibility plan.
- [ ] Every exposed Management API appears exactly once in `docs/management-api-contracts.md`.
- [ ] Existing Management API meanings remain backward compatible or use a new versioned contract ID.
- [ ] The documented compatibility candidate has been accepted using live evidence before 1.0.

## Architecture

- [ ] No GamerHQ bot/cog/service/database/host imports.
- [ ] No Discord.py imports.
- [ ] No Recurring Posts dependency.
- [ ] Scheduling uses the public Runtime scheduler.
- [ ] Provider-specific ingestion remains behind CreativeSource boundaries.
- [ ] Cross-repository requirements are represented by a handoff, not hidden coupling.
- [ ] Campaign aggregate mutations remain protected by the documented per-guild storage boundary.

## Security

- [ ] No real Awin token exists in source, tests, examples, screenshots or history.
- [ ] Token remains in encrypted Skill secret storage only.
- [ ] Diagnostics and health contain no credential material.
- [ ] Failure history contains generic codes, not raw exceptions.
- [ ] Saved HTML remains treated as untrusted input.
- [ ] Imported and rendered tracking/image URLs require supported HTTPS Awin URLs.
- [ ] URL credentials are rejected.
- [ ] Repository/history secret scan is clean where available.
- [ ] Live acceptance evidence is redacted according to `docs/live-acceptance-report-template.md`.

## Functional tests

- [ ] Setup/token rejection.
- [ ] Publisher discovery/selection.
- [ ] Advertiser discovery.
- [ ] Manual HTML parsing.
- [ ] Saved-page multi-advertiser import.
- [ ] Authoritative missing/restored transitions.
- [ ] Creative enable/disable.
- [ ] Post preview/confirmation.
- [ ] Exact `confirmPayload` forwarding is documented and tested.
- [ ] Stale Creative revalidation.
- [ ] Campaign create/edit/pause/resume/delete.
- [ ] Fixed/sequential/random/shuffle rotation.
- [ ] Failed send does not advance rotation.
- [ ] Parallel Campaign/History operations preserve every tested update.
- [ ] Campaign history remains bounded.
- [ ] Secret-redaction diagnostics tests.
- [ ] Complete offline V1 acceptance flow.
- [ ] Management-contract documentation inventory matches the manifest.

## CI and artifacts

- [ ] Python 3.12 passes.
- [ ] Python 3.13 passes.
- [ ] Python 3.14 passes.
- [ ] Pinned reviewed GamerHQ Skill SDK commit is used.
- [ ] Wheel builds successfully.
- [ ] Built wheel installs and imports outside the source tree.
- [ ] Source distribution builds successfully for a stable release.
- [ ] `pip check` passes.
- [ ] Final artifacts are built from the exact reviewed release commit/tag.

## Live acceptance before 1.0

- [ ] Issue #18 uses the exact reviewed Skill commit/version.
- [ ] `docs/live-acceptance.md` is executed on an isolated compatible host.
- [ ] `docs/live-acceptance-report-template.md` is completed with redacted evidence.
- [ ] Real token verification and publisher selection pass.
- [ ] Joined advertiser discovery passes.
- [ ] Real My Creative HTML import passes.
- [ ] Creative preview and enable/disable pass.
- [ ] Preview-confirmed Post Now passes.
- [ ] Campaign create/Preview Next/Run Now/pause-resume/history pass.
- [ ] Restart recovery preserves state and creates no duplicate jobs or sends.
- [ ] Diagnostics contain no credential material.
- [ ] Real provider payloads fit the documented compatibility candidate or an explicit repository-owned adjustment is completed.
- [ ] No unresolved Skill-owned functional/security blocker remains.

## Owner release decisions

- [ ] Issue #23 identifies the intended license.
- [ ] Copyright holder/legal identity is confirmed.
- [ ] Approved `LICENSE` file exists.
- [ ] Initial distribution channel is confirmed.
- [ ] PyPI ownership/trusted publishing is configured when PyPI is selected.

## Stable release publication

- [ ] Release branch/PR contains only approved release preparation.
- [ ] Changelog entry is final.
- [ ] Package/manifest/tests report the same version.
- [ ] Immutable `v<version>` tag points to the reviewed `main` commit.
- [ ] GitHub Release exists.
- [ ] Wheel and source distribution are attached or otherwise published through the approved channel.
- [ ] Release notes include public-contract, migration, security and known-limitation impact.
- [ ] Release notes state that this Skill release does not authorize a downstream GamerHQ deployment.
- [ ] Post-release `main` CI is green.

## Downstream adoption boundary

A downstream Host may additionally verify package pinning, UI rendering, backups and deployment rollback. Those operational decisions remain owned by that Host.

A green Skill CI or published Skill release does not itself authorize a downstream production deployment.
