# Awin Affiliate Skill repository instructions

## Repository ownership

Repository:

`Duy-Phan96/gamerhq-skill-awin-affiliate`

This repository is autonomous.

It owns:

- Awin provider integration and Creative-source adapters;
- Skill manifest, capabilities and public Management contracts;
- Awin setup, advertiser discovery, Creative Library behavior, posting, campaigns, history and diagnostics;
- Skill-owned storage identities and migrations;
- this package's tests, CI, issues, branches, pull requests, versioning, releases and documentation.

It does not own:

- `Duy-Phan96/GamerHQ` Host/UI/deployment internals;
- `gamerhq-web`;
- GamerHQ Runtime/SDK implementation;
- another `gamerhq-skill-*` repository;
- another project's release process.

Read-only inspection of external repositories is allowed only to understand public contracts, released versions, immutable commits, compatibility and documentation.

Do not create branches, commits or pull requests in another repository from this project.

## Public dependency boundary

This package is a portable GamerHQ Skill.

Consume only public Runtime / SDK contracts.

Current compatibility target:

- Runtime API: `1`
- SDK: `>=0.1,<0.2`

Current public capabilities consumed:

- `storage.skill`
- `secrets.skill`
- `http.external`
- Discord channel/message/embed/link-button capabilities declared by the manifest
- `scheduler.jobs`
- `audit.write`

If a required public Runtime/SDK/Host contract is missing, do not implement it in another repository.

Create a handoff that describes the missing public behavior and stop cross-repository implementation.

## Handoff rule

Use handoffs instead of cross-repository changes.

Required format:

```text
HANDOFF REQUIRED

FROM REPOSITORY:
Duy-Phan96/gamerhq-skill-awin-affiliate

TARGET REPOSITORY:
<owning repository>

PROBLEM:
<missing public capability or integration behavior>

WHY THIS BELONGS TO THE TARGET:
<ownership/architecture reason>

REQUESTED OUTCOME:
<public behavior or contract needed>

CURRENT CONTRACT / VERSION:
<Runtime API / SDK / Management API / Skill version>

ACCEPTANCE CRITERIA:
- ...

COMPATIBILITY / MIGRATION CONSTRAINTS:
- ...

SECURITY / CAPABILITY IMPACT:
- ...

NON-GOALS:
- ...

SOURCE PROJECT STATUS:
<what is complete here and what remains blocked>

WHEN COMPLETE:
<released version / immutable commit / API this project should consume>
```

The handoff specifies what is needed. The receiving repository owns its implementation decision.

## Independent releases

This Skill releases independently.

Use repository-local release states such as:

- READY FOR REVIEW
- READY FOR RELEASE
- RELEASED
- BLOCKED BY HANDOFF
- WAITING FOR PUBLIC CONTRACT
- COMPATIBLE WITH RUNTIME API 1

A green Skill release never implies that the GamerHQ production server should update.

GamerHQ Host may independently choose whether and when to install/pin a released Skill.

## Third-party developer model

Treat this repository as if it were maintained by an independent third-party Skill developer.

The Skill may use public SDK contracts and request new public capabilities.

It must not assume permission to change GamerHQ Host internals, deployment infrastructure, another Skill, or gamerhq-web.

## Hard rules

- Keep Skill ID `awin-affiliate` stable.
- Do not import Discord.py or GamerHQ bot/cogs/services/database/hosts/config.
- Use only public `skill_runtime` contracts for host capabilities.
- Do not depend on the Recurring Posts Skill or Amazon Affiliate Skill.
- Awin-specific scheduling, rotation and campaign state belong to this Skill.
- Keep credentials out of logs, fixtures, examples and repository history.
- Do not implement authenticated scraping until official Awin capabilities have been checked.
- Isolate every Creative source behind a provider adapter.
- Manual HTML imports must never mark unmentioned Creatives as missing.
- Keep tests offline and token-free.
- Preserve stable storage keys and Management contract IDs across compatible releases.
- Do not create a central orchestrator for other GamerHQ repositories.

## Skill-to-Skill communication

Never import another Skill's private implementation.

Optional cross-Skill behavior must use public Events or Skill APIs and remain functional when the provider is absent unless the dependency is explicitly declared required.

## Reporting

At meaningful milestones report:

```text
COMPLETED

REPOSITORY
BRANCH
PR
VERSION / MERGE COMMIT

TESTS / CI

PUBLIC CONTRACT IMPACT

STORAGE / MIGRATION IMPACT

SECURITY / CAPABILITY IMPACT

RELEASE STATUS

DEPENDENCIES

HANDOFFS REQUIRED

PROPOSED FOLLOW-UPS
```

If another repository must change, stop at the handoff.
