# Release process

This repository releases the standalone Awin Affiliate Skill independently from every downstream host.

A successful Skill release does **not** authorize, schedule or imply a GamerHQ Host or production-server deployment.

## Release states

Use the following repository-local states:

- `IN DEVELOPMENT` — normal repository work;
- `READY FOR REVIEW` — focused branch/PR complete, CI pending or under review;
- `READY FOR LIVE ACCEPTANCE` — automated gates pass and the live runbook can be executed;
- `BLOCKED BY LIVE ACCEPTANCE` — real provider/host validation remains outstanding;
- `READY FOR RELEASE` — live acceptance and owner decisions are complete;
- `RELEASED` — immutable tag and release artifacts are published;
- `BLOCKED BY HANDOFF` — a required public external contract is unavailable.

## Versioning

Use semantic versioning.

- patch: compatible bug, security, documentation or hardening release;
- minor: additive compatible capability before or after 1.0;
- major: incompatible public contract or storage compatibility break.

Stable identity:

```text
Skill ID: awin-affiliate
Runtime API: 1
Entry point: gamerhq.skills / awin-affiliate
```

Public `.v1` Management contracts, documented storage keys, the secret key and scheduler-handler identity form the proposed 1.0 compatibility baseline.

The package-owned runtime version is exposed as:

```python
from gamerhq_skill_awin_affiliate import __version__
```

`pyproject.toml`, `__version__`, and every runtime-visible Skill manifest must agree.

## Approved legal and distribution baseline

The repository owner approved the following baseline for the first stable release:

```text
License: MIT
Copyright holder: Duy Phan
Package author: Duy Phan
Initial distribution: GitHub Release only
PyPI: deferred
```

The authoritative legal notice is the repository-root `LICENSE` file.

The detailed decision record is `docs/legal-and-distribution.md`.

PyPI is not part of the `1.0.0` release. A future PyPI publication requires a separate owner decision covering package ownership, trusted publishing or credentials, support expectations and rollback.

## Normal change workflow

1. Create or identify a clear Issue for substantial work.
2. Branch from current `main`.
3. Implement one coherent repository-owned slice.
4. Add focused regression tests.
5. Update documentation and `CHANGELOG.md`.
6. Open a PR that states:
   - behavior and rationale;
   - tests and CI;
   - public-contract impact;
   - storage/migration impact;
   - security/capability impact;
   - dependencies and handoffs;
   - release status.
7. Merge only after the complete CI matrix passes.
8. Verify the post-merge `main` CI run.
9. For release-readiness claims, verify the exact post-merge `main` artifact dry run as well as the normal Skill CI run.

## Repository release preflight

Run the repository-local preflight before building or reviewing release artifacts:

```bash
python -m tools.release_preflight
```

The preflight verifies:

- package name and semantic version identity;
- `pyproject.toml`, package constant, base/hardened/exported manifests;
- stable Skill ID, Runtime API and entry point;
- capability metadata versus the executable manifest;
- README and changelog version state;
- exact Management API documentation inventory;
- an approved `LICENSE` file and non-blocked README status for stable `1.x` candidates.

CI runs this command before building the wheel. A release PR must not bypass or weaken these checks to make an inconsistent candidate pass.

## Automated release gates

The current CI must pass on:

- Python 3.12;
- Python 3.13;
- Python 3.14.

For each version, CI must:

1. install the pinned reviewed GamerHQ Skill SDK;
2. run the repository release preflight;
3. build the Skill wheel;
4. install the built wheel;
5. verify installed distribution metadata, package version and Skill manifest outside the source tree;
6. run `pip check`;
7. run the complete offline suite.

Before a stable release, build both a wheel and source distribution:

```bash
python -m pip install build==1.6.1
python -m build
python -m tools.verify_release_artifacts --write-checksums
```

Expected artifacts:

```text
dist/gamerhq_skill_awin_affiliate-<version>-py3-none-any.whl
dist/gamerhq_skill_awin_affiliate-<version>.tar.gz
dist/SHA256SUMS.txt
```

## Non-publishing artifact dry run

The repository includes:

```text
.github/workflows/release-artifact-dry-run.yml
```

The workflow runs:

- on pull requests, validating the proposed merged tree before review and merge;
- on every push to `main`, validating the exact post-merge commit;
- through manual `workflow_dispatch` when an explicit rerun is needed.

The workflow:

- runs the release preflight;
- builds wheel and source distribution from the same commit;
- verifies filenames, metadata and required contents;
- clean-install-tests the wheel in one virtual environment;
- clean-install-tests the source distribution in another virtual environment;
- verifies distribution version, package `__version__`, Skill manifest version, Skill ID and Runtime API outside the source tree;
- generates SHA-256 checksums;
- uploads temporary GitHub Actions artifacts for review.

Pull-request evidence proves the proposed tree. It does not replace the successful `main`-push run for the exact reviewed post-merge commit. Release-readiness claims and final release preparation must cite that exact-main evidence.

This workflow is verification only. It must not create a tag, GitHub Release, PyPI publication or downstream deployment.

See `docs/release-artifact-dry-run.md` for details.

## 1.0.0 entry gates

Do not prepare or merge the final `1.0.0` release PR until:

- Issue #18 live acceptance is complete;
- the acceptance report records a PASS;
- no unresolved Skill-owned functional/security blocker remains;
- `docs/management-api-contracts.md` is accepted as the stable V1 baseline;
- storage, secret and scheduler identities are accepted;
- the approved MIT / Duy Phan / GitHub Release only baseline is implemented;
- the approved `LICENSE` file exists and package author metadata names Duy Phan;
- Issue #33 branch protection is enabled, or the owner records an explicit temporary exception before the release PR;
- release checklist is complete.

## Stable release preparation

Create a focused release branch, for example:

```text
release/1.0.0
```

The release PR should contain only release preparation and approved final corrections.

Required changes:

- update `pyproject.toml` version;
- update `gamerhq_skill_awin_affiliate/_version.py`;
- confirm base, hardened and exported Skill manifests resolve to the same package version;
- update version assertions/tests;
- promote the matching `CHANGELOG.md` section;
- update project status from blocked to ready/released as appropriate;
- confirm the approved MIT `LICENSE` and Duy Phan package-author metadata remain unchanged;
- confirm README and contract documentation reflect the release;
- run `python -m tools.release_preflight`;
- run the release-artifact dry run;
- build and install-test wheel and source distribution;
- prepare release notes.

## Tag and GitHub Release

After the release PR is merged and post-merge `main` CI is green:

1. verify the exact post-merge `main` artifact dry run is green;
2. create immutable tag `v<version>` from that exact reviewed `main` commit;
3. verify the tag points to that commit;
4. create a GitHub Release from the tag;
5. attach the wheel and source distribution;
6. attach `SHA256SUMS.txt` or publish equivalent checksums;
7. publish concise release notes with compatibility, security and migration impact;
8. state explicitly that downstream hosts choose their own adoption/deployment timing.

Do not move an existing release tag.

## PyPI

PyPI is deliberately deferred and is not part of the `1.0.0` release.

A future PyPI publication requires a separate owner decision confirming:

- package-name ownership;
- publisher account or organization;
- trusted publishing or secure release credentials;
- support expectations;
- rollback and correction procedures.

No PyPI credential, publication workflow or package upload should be added to the first stable release.

## Release notes template

```markdown
# Awin Affiliate <version>

## Summary

## User-visible changes

## Public contract impact

## Storage / migration impact

## Security / capability impact

## Compatibility

## Tests and artifacts

## Known limitations

## Downstream adoption boundary

This Skill release does not authorize or imply a GamerHQ Host or production deployment.
```

## Rollback

A package rollback means selecting the previous reviewed immutable Skill release/tag in a downstream host.

Repository responsibilities:

- preserve previous release tags;
- document storage or migration implications;
- never silently rewrite released artifacts;
- publish a corrective patch when a released defect belongs to this Skill.

Downstream hosts own their package pin, deployment, backup and operational rollback process.

## Hotfixes

For a critical released defect:

1. reproduce and document the issue;
2. create a focused hotfix branch from the affected stable line or current `main` as appropriate;
3. add a regression test;
4. issue a compatible patch release;
5. document the impact and any downstream adoption urgency;
6. do not deploy another repository from this project.
