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

## Automated release gates

The current CI must pass on:

- Python 3.12;
- Python 3.13;
- Python 3.14.

For each version, CI must:

1. install the pinned reviewed GamerHQ Skill SDK;
2. build the Skill wheel;
3. install the built wheel;
4. verify the installed package outside the source tree;
5. run `pip check`;
6. run the complete offline suite.

Before a stable release, also build a source distribution locally or in a release workflow:

```bash
python -m pip install build
python -m build
```

Expected artifacts:

```text
dist/gamerhq_skill_awin_affiliate-<version>-py3-none-any.whl
dist/gamerhq_skill_awin_affiliate-<version>.tar.gz
```

## 1.0.0 entry gates

Do not prepare or merge the final `1.0.0` release PR until:

- Issue #18 live acceptance is complete;
- the acceptance report records a PASS;
- no unresolved Skill-owned functional/security blocker remains;
- `docs/management-api-contracts.md` is accepted as the stable V1 baseline;
- storage, secret and scheduler identities are accepted;
- Issue #23 license identity and distribution decisions are resolved;
- release checklist is complete.

## Stable release preparation

Create a focused release branch, for example:

```text
release/1.0.0
```

The release PR should contain only release preparation and approved final corrections.

Required changes:

- update `pyproject.toml` version;
- update `SkillManifest.version`;
- update version assertions/tests;
- promote the matching `CHANGELOG.md` section;
- update project status from blocked to ready/released as appropriate;
- add or update the approved `LICENSE` file;
- confirm README and contract documentation reflect the release;
- build and install-test wheel and source distribution;
- prepare release notes.

## Tag and GitHub Release

After the release PR is merged and post-merge `main` CI is green:

1. create immutable tag `v<version>` from the exact reviewed `main` commit;
2. verify the tag points to that commit;
3. create a GitHub Release from the tag;
4. attach the wheel and source distribution;
5. include checksums where practical;
6. publish concise release notes with compatibility, security and migration impact;
7. state explicitly that downstream hosts choose their own adoption/deployment timing.

Do not move an existing release tag.

## PyPI

PyPI publication is optional and remains blocked until Issue #23 explicitly confirms:

- package-name ownership;
- publisher account/organization;
- trusted publishing or secure release credentials;
- support and rollback expectations.

A GitHub Release with tested artifacts is a valid initial distribution model.

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
