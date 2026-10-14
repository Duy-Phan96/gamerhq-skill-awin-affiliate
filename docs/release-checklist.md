# Release readiness checklist

Use this checklist before promoting a reviewed Awin Affiliate Skill version.

The detailed workflow is in `docs/release-process.md`.

## Package and contracts

- [ ] Skill ID remains `awin-affiliate`.
- [ ] Package entry point matches the Skill ID.
- [ ] `pyproject.toml`, package `__version__`, and base/hardened/exported Skill manifests report the same semantic version.
- [ ] Runtime API compatibility is documented.
- [ ] Package capability metadata matches the executable manifest.
- [ ] Stable storage keys have not changed without a migration.
- [ ] Secret and scheduler-handler identities have not changed without an explicit compatibility plan.
- [ ] Every exposed Management API appears exactly once in `docs/management-api-contracts.md`.
- [ ] Existing Management API meanings remain backward compatible or use a new versioned contract ID.
- [ ] The documented compatibility candidate has been accepted using live evidence before 1.0.
- [ ] `python -m tools.release_preflight` passes.

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
- [ ] Release-preflight drift tests cover package versions and stable-license requirements.
- [ ] Stable-release preflight tests reject missing, non-PASS and placeholder live-acceptance attestations.
- [ ] Artifact-verifier tests reject missing files and incorrect metadata.
- [ ] Checksum-generation tests cover wheel and source distribution.
- [ ] License/distribution regression tests match `docs/legal-and-distribution.md`.

## CI and artifacts

- [ ] Python 3.12 passes.
- [ ] Python 3.13 passes.
- [ ] Python 3.14 passes.
- [ ] Pinned reviewed GamerHQ Skill SDK commit is used.
- [ ] Repository release preflight runs before artifact build.
- [ ] Wheel builds successfully.
- [ ] Built wheel installs and imports outside the source tree.
- [ ] Installed distribution metadata matches package `__version__` and the executable Skill manifest.
- [ ] Source distribution builds successfully.
- [ ] Wheel and source distribution are built from the same reviewed commit.
- [ ] `python -m tools.verify_release_artifacts --write-checksums` passes.
- [ ] Wheel clean-install acceptance passes in an isolated virtual environment.
- [ ] Source-distribution clean-install acceptance passes in a separate isolated virtual environment.
- [ ] `SHA256SUMS.txt` covers both artifact formats.
- [ ] Non-publishing dry-run artifacts are available for review in GitHub Actions.
- [ ] `pip check` passes.
- [ ] Final artifacts are built from the exact reviewed release commit/tag.

## Live acceptance before 1.0

- [ ] Issue #18 uses the exact reviewed Skill commit/version.
- [ ] `docs/live-acceptance.md` is executed on an isolated compatible host.
- [ ] `docs/live-acceptance-report-template.md` is copied to `docs/live-acceptance-report.md`.
- [ ] `docs/live-acceptance-report.md` contains only redacted evidence.
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
- [ ] `LIVE_ACCEPTANCE_STATUS=PASS` is recorded only after the complete run passes.
- [ ] `LIVE_ACCEPTANCE_APPROVED_BY` contains a real approver identity.
- [ ] `LIVE_ACCEPTANCE_APPROVED_AT` uses `YYYY-MM-DD`.
- [ ] `LIVE_ACCEPTANCE_REVIEWED_COMMIT` contains the accepted lowercase 40-character commit SHA.

## Approved legal and distribution baseline

- [ ] Root `LICENSE` is the approved MIT text.
- [ ] Copyright notice is `Copyright (c) 2026 Duy Phan`.
- [ ] Package author metadata names `Duy Phan`.
- [ ] `docs/legal-and-distribution.md` matches the release preparation.
- [ ] Initial distribution remains **GitHub Release only**.
- [ ] Wheel, source distribution and `SHA256SUMS.txt` are attached to the GitHub Release.
- [ ] No PyPI credentials, workflow or publication are included in the 1.0 release.

## Repository protection

- [ ] Issue #33 branch protection is enabled, or the owner records an explicit temporary exception before the release PR.
- [ ] Required checks match the current workflow names.
- [ ] Force pushes and deletion of `main` are blocked when branch protection is enabled.

## Stable release publication

- [ ] Release branch/PR contains only approved release preparation.
- [ ] Changelog entry is final.
- [ ] Package metadata, package `__version__`, and every runtime-visible manifest report the same version.
- [ ] README no longer reports `BLOCKED BY LIVE ACCEPTANCE` for a stable 1.x candidate.
- [ ] Stable preflight accepts the approved `docs/live-acceptance-report.md` attestation.
- [ ] Release-artifact dry run passes on the exact release-candidate commit.
- [ ] Immutable `v<version>` tag points to the reviewed `main` commit.
- [ ] GitHub Release exists.
- [ ] Wheel, source distribution and checksums are attached to the GitHub Release.
- [ ] Published artifact checksums match the reviewed dry-run/release build.
- [ ] Release notes include public-contract, migration, security and known-limitation impact.
- [ ] Release notes state that this Skill release does not authorize a downstream GamerHQ deployment.
- [ ] Post-release `main` CI is green.

## Downstream adoption boundary

A downstream Host may additionally verify package pinning, UI rendering, backups and deployment rollback. Those operational decisions remain owned by that Host.

A green Skill CI or published Skill release does not itself authorize a downstream production deployment.
