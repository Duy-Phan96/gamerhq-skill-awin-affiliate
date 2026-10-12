# Security

## Scope

This repository is a portable external GamerHQ Skill. It must use only public Skill Runtime / SDK capabilities and must never import GamerHQ host internals.

## Credentials

The Awin access token is stored only through the public encrypted Skill secret-store port.

Stable secret key:

```text
awin-access-token.v1
```

The token must never be:

- committed to Git;
- stored in normal Skill JSON storage;
- returned by Management APIs;
- written to audit metadata;
- placed in diagnostics;
- copied into fixtures, screenshots or documentation;
- included in exception messages.

Connection status exposes only whether a token is stored. A masked compatibility marker, where present in the setup-status contract, is not a recoverable credential and must not be copied into diagnostics.

## External HTTP

All Awin API requests go through the host-mediated `http.external` port.

The Skill does not receive the host HTTP client, environment or network configuration directly.

## Discord and outbound URLs

Portable Skill code never imports Discord.py.

Discord access is limited to declared public capabilities:

- channel reads;
- message sends;
- embeds;
- safe HTTPS link buttons.

Mentions are disabled for affiliate posts.

Imported tracking and image URLs must:

- use HTTPS;
- resolve to a supported Awin host at import time;
- contain no URL username/password component.

Posting validates HTTPS again before constructing a Discord payload so malformed or legacy persisted values fail closed.

## Saved HTML

Saved My Creative HTML is treated as untrusted input.

The parser:

- only accepts supported HTTPS Awin tracking/image URLs;
- extracts stable IDs from Awin query parameters;
- rejects unsupported/non-Awin URLs and URL credentials;
- does not execute HTML, JavaScript or embedded scripts;
- does not automate an Awin login session.

A saved page may be incomplete. Missing detection is therefore disabled unless one advertiser is explicitly confirmed as a complete snapshot.

## Campaign data integrity

Campaigns and their bounded delivery history are shared aggregate values per guild. Every aggregate read-modify-write cycle is protected by a per-guild campaign-store lock, while a separate per-campaign execution lock prevents Run Now, scheduled execution and management mutations for the same campaign from overwriting one another.

Scheduler changes use best-effort persisted-state compensation on failure. The public storage port does not provide a transaction spanning multiple keys, so successful Discord delivery state is persisted before history where both writes cannot be atomic.

## Failure handling

Persisted campaign history stores bounded, generic outcomes only.

Examples:

```text
sent
blocked
failed
discord-send-failed
campaign-state-missing-after-send
```

Raw provider/Discord exception text must not be persisted.

## Reporting a security issue

Do not open a public issue containing credentials, private user data or exploitable secret material.

Report the issue privately to the repository owner and include only the minimum redacted reproduction information needed to investigate.

If a real credential is exposed, revoke/rotate it at the provider before continuing investigation.
