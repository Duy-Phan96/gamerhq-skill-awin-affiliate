# Release artifact dry run

This repository provides a non-publishing workflow that proves the release artifacts can be built, inspected and installed before a stable release is authorized.

Workflow:

```text
.github/workflows/release-artifact-dry-run.yml
```

## Triggers and evidence scope

The workflow runs:

- on pull requests, validating the proposed merged tree before review/merge;
- on every push to `main`, validating the exact post-merge commit;
- through manual `workflow_dispatch` when an explicit rerun is needed.

Release-readiness claims must use the successful `main`-push run for the exact reviewed commit. A pull-request run proves the proposed tree but is not a substitute for post-merge commit evidence.

## What it does

The workflow:

1. installs the pinned reviewed GamerHQ Skill SDK;
2. installs the pinned Python Packaging Authority build frontend;
3. runs `python -m tools.release_preflight`;
4. builds both artifact formats with `python -m build`;
5. verifies wheel and source-distribution names, metadata and required contents;
6. installs the wheel in a clean virtual environment;
7. installs the source distribution in a separate clean virtual environment;
8. imports the Skill outside the repository source tree;
9. verifies distribution version, package `__version__`, Skill manifest version, Skill ID and Runtime API;
10. writes `dist/SHA256SUMS.txt`;
11. uploads the dry-run files as a short-lived GitHub Actions artifact.

## Artifact verifier

Run locally after building:

```bash
python -m tools.verify_release_artifacts --write-checksums
```

Expected files:

```text
dist/gamerhq_skill_awin_affiliate-<version>-py3-none-any.whl
dist/gamerhq_skill_awin_affiliate-<version>.tar.gz
dist/SHA256SUMS.txt
```

The verifier checks:

- exactly one wheel and one source distribution;
- expected normalized filenames;
- package name and version in wheel `METADATA` and source `PKG-INFO`;
- `py3-none-any` wheel tagging;
- required runtime modules in the wheel;
- required source, documentation, tests and release tools in the source distribution;
- inclusion of `LICENSE` in the source distribution once an approved file exists.

## Source-distribution contents

`MANIFEST.in` defines the repository-owned source-distribution additions:

- core project documentation;
- detailed docs;
- offline tests;
- repository-local release tools.

Runtime consumers still install only the `gamerhq_skill_awin_affiliate` package from the wheel.

## Security and publication boundary

The dry run does **not**:

- create or move a Git tag;
- create a GitHub Release;
- publish to PyPI;
- use an Awin credential;
- deploy a downstream Host;
- authorize a GamerHQ production update.

Uploaded workflow artifacts are temporary verification evidence, not a formal release.

## Relationship to 1.0

The final `1.0.0` release workflow may reuse these proven steps only after:

- Issue #18 live acceptance passes;
- the redacted acceptance report is approved;
- Issue #23 resolves license identity and distribution;
- the stable release preflight passes;
- the dedicated release PR and post-merge CI are green;
- the exact final `main` commit has a successful artifact dry-run result.
