# Legal identity and initial distribution

This document records the repository owner's approved legal and distribution baseline for the first stable Awin Affiliate release.

## License

The project is licensed under the MIT License.

Copyright holder:

```text
Duy Phan
```

Copyright notice:

```text
Copyright (c) 2026 Duy Phan
```

The authoritative license text is the repository-root `LICENSE` file.

Package metadata must remain aligned with this decision:

```toml
license = {text = "MIT"}
authors = [{name = "Duy Phan"}]
```

Changes to the license, copyright holder or package-author identity require a new explicit owner decision and must not be inferred from branding, repository names or downstream hosts.

## Initial stable distribution

The approved initial distribution channel for `1.0.0` is:

```text
GitHub Release only
```

The stable release must provide:

- an immutable `v1.0.0` Git tag;
- a GitHub Release created from that exact tag;
- the reviewed wheel;
- the reviewed source distribution;
- `SHA256SUMS.txt` or equivalent published checksums;
- release notes covering compatibility, security, migration and known limitations.

## PyPI

PyPI is deliberately deferred and is not part of the `1.0.0` release.

A future PyPI publication requires a separate owner decision covering:

- package-name ownership;
- publisher account or organization;
- trusted publishing or secure credentials;
- support expectations;
- rollback and correction procedures.

No PyPI credential, workflow or publication should be introduced as part of the first stable release.

## Downstream boundary

Publishing this Skill does not authorize, schedule or imply a GamerHQ Host or production-server deployment.

Each downstream host independently chooses whether and when to adopt an immutable Skill release.
