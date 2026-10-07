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

Connection status exposes only whether a token is stored.

## External HTTP

All Awin API requests go through the host-mediated `http.external` port.

The Skill does not receive the host HTTP client, environment or network configuration directly.

## Discord

Portable Skill code never imports Discord.py.

Discord access is limited to declared public capabilities:

- channel reads;
- message sends;
- embeds;
- safe HTTPS link buttons.

Mentions are disabled for affiliate posts.

## Saved HTML

Saved My Creative HTML is treated as untrusted input.

The parser:

- only accepts supported Awin tracking/image URLs;
- extracts stable IDs from Awin query parameters;
- rejects unsupported/non-Awin URLs;
- does not execute HTML, JavaScript or embedded scripts;
- does not automate an Awin login session.

A saved page may be incomplete. Missing detection is therefore disabled unless one advertiser is explicitly confirmed as a complete snapshot.

## Failure handling

Persisted campaign history stores bounded, generic outcomes only.

Examples:

```text
sent
blocked
failed
discord-send-failed
```

Raw provider/Discord exception text must not be persisted.

## Reporting a security issue

Do not open a public issue containing credentials, private user data or exploitable secret material.

Report the issue privately to the repository owner and include only the minimum redacted reproduction information needed to investigate.

If a real credential is exposed, revoke/rotate it at the provider before continuing investigation.
