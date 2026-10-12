## Summary

<!-- What repository-owned problem does this PR solve, and why now? -->

Closes #

## User-visible behavior

<!-- Describe observable behavior. Write "None" for internal-only changes. -->

## Scope and repository boundary

- [ ] This PR changes only `gamerhq-skill-awin-affiliate`.
- [ ] Any required external work is documented as a `HANDOFF REQUIRED`, not implemented here.
- [ ] No unrelated feature or cleanup is bundled into this PR.

## Tests and evidence

<!-- List focused tests, full-suite result, release preflight, and artifact dry-run evidence as applicable. -->

- [ ] Focused regression coverage added or not required with explanation.
- [ ] `python -m tools.release_preflight` passes.
- [ ] Python 3.12 / 3.13 / 3.14 CI passes.
- [ ] Wheel verification passes.
- [ ] Release artifact dry run passes when packaging/release behavior changes.

## Public contract impact

<!-- Management API IDs, request/response meaning, Runtime API, Skill ID, entry point. -->

- [ ] No incompatible `.v1` Management contract change.
- [ ] Additive or incompatible contract changes are documented and versioned deliberately.

## Storage and migration impact

<!-- Stable storage keys, secret key, scheduler handler, migration or rollback implications. -->

## Security and capability impact

<!-- Credentials, HTTP, Discord, untrusted HTML, permissions/capabilities, disclosure behavior. -->

- [ ] No real token, production secret, private database, personal data, or unredacted private payload is included.
- [ ] Capability changes, if any, are reflected in package metadata, manifest, tests, and docs.

## Release status

<!-- IN DEVELOPMENT / READY FOR REVIEW / BLOCKED BY HANDOFF / release-specific state. -->

## Documentation

- [ ] Relevant README, contract, architecture, security, release, or changelog documentation is updated.
- [ ] Historical decisions were preserved rather than silently overwritten.

## Final checklist

- [ ] The change follows `AGENTS.md` and `CONTRIBUTING.md`.
- [ ] The implementation is the smallest reliable solution for the approved scope.
- [ ] No downstream GamerHQ deployment is implied or performed by this PR.
