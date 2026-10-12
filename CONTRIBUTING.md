# Contributing to Awin Affiliate

Thank you for helping improve the standalone `awin-affiliate` Skill.

## Repository scope

This repository owns the Awin Affiliate Skill package, its provider integration, public Management contracts, Skill-owned storage, tests, documentation and independent releases.

It does **not** own GamerHQ Host/UI/deployment internals, the Runtime/SDK implementation, gamerhq-web or another Skill repository.

When an external public capability is missing, document a `HANDOFF REQUIRED` request according to `AGENTS.md`. Do not modify another repository from this project.

## Development environment

Requirements:

- Python 3.12 or newer;
- Git;
- the reviewed GamerHQ Skill SDK revision used by CI.

The current CI SDK commit is defined as `GAMERHQ_SDK_REF` in `.github/workflows/tests.yml`.

Example local setup:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "gamerhq-skill-sdk @ git+https://github.com/Duy-Phan96/GamerHQ.git@c27260e8831115f8cf78cc58d5322dbdd101a563"
python -m pip install -e .
python -m pip install pytest==9.1.1
```

## Tests

Run the full offline suite:

```bash
python -m pytest
```

Build and inspect the installable package:

```bash
python -m pip wheel --no-deps . --wheel-dir dist
python -m pip install --no-deps --force-reinstall dist/*.whl
python -m pip check
```

Tests must not require:

- a real Awin token;
- a live Discord server;
- a production database;
- another repository's private implementation;
- unrestricted internet access.

Use fake public Runtime ports for HTTP, secrets, storage, Discord, scheduler and audit behavior.

## Security rules

Never commit or paste:

- an Awin access token;
- `GAMERHQ_SKILL_SECRET_KEY`;
- production `.env` values;
- private runtime databases;
- raw provider/Discord exception payloads containing private data.

Use synthetic values in fixtures. If a real credential is exposed, revoke or rotate it before further investigation.

Saved HTML is untrusted input. New ingestion paths must preserve the HTTPS, supported-host and explicit-authority boundaries documented in `SECURITY.md`.

## Branch and pull-request workflow

Use a focused branch from `main`, for example:

```text
fix/campaign-history-race
feat/awin-offers-v1
docs/provider-acceptance
```

A pull request should:

- solve one coherent repository-owned problem;
- reference its Issue when one exists;
- include tests for behavioral changes;
- update relevant documentation and `CHANGELOG.md`;
- state public-contract, storage, migration, security and capability impact;
- avoid unrelated cleanup or cross-repository implementation;
- pass the complete Python 3.12/3.13/3.14 wheel-install CI matrix.

## Compatibility rules

Before 1.0, changes should still be deliberate because downstream hosts already consume the current contracts.

After 1.0:

- preserve stable Skill ID `awin-affiliate`;
- preserve documented `.v1` Management API meanings;
- use a new versioned contract ID for incompatible API changes;
- preserve storage/secret/scheduler identities or provide an explicit migration;
- do not silently change authority, disclosure or credential behavior.

The detailed compatibility candidate is documented in `docs/management-api-contracts.md`.

## Definition of Done

A change is complete when:

- behavior is implemented in this repository;
- focused regression tests exist;
- the full suite passes;
- the built wheel imports outside the source tree;
- documentation reflects the actual implementation;
- no secret or production data is included;
- public-contract and migration impact is explicit;
- required external work is represented by a handoff rather than hidden coupling.

## Releases

Release preparation follows `docs/release-process.md` and `docs/release-checklist.md`.

A Skill release is independent. It never authorizes or implies a downstream GamerHQ production deployment.
