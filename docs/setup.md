# Setup

## Requirements

- Python 3.12 or newer.
- A GamerHQ-compatible host implementing Runtime API 1.
- GamerHQ Skill SDK compatible with `>=0.1,<0.2`.
- Host capabilities required by the current Skill manifest.
- An Awin publisher account only for authenticated API setup/discovery.

The normal offline test suite does not require an Awin account or Discord token.

## Package identity

```text
Package: gamerhq-skill-awin-affiliate
Skill ID: awin-affiliate
Runtime API: 1
Entry point group: gamerhq.skills
```

The Skill ID is stable and must not be renamed.

## Required capabilities

Current package metadata/manifest declare:

```text
storage.skill
secrets.skill
http.external
discord.channels.read
discord.messages.send
discord.embeds.send
scheduler.jobs
audit.write
```

The host must fail activation when a required capability is unavailable.

## Install in a GamerHQ host

Production/development hosts should install a reviewed immutable package artifact or commit according to the GamerHQ external Skill workflow.

Do not configure a moving Git branch as a production dependency.

After package discovery, the host should show:

```text
/server manage
→ Skills
→ Awin Affiliate
```

Host rendering is implemented separately from this repository and must use public Management APIs only.

## Connect Awin

Intended flow:

```text
Connect Awin
→ enter access token
→ verify token against Awin
→ discover publisher accounts
→ auto-select one publisher or choose from multiple accounts
```

The raw token is stored through `ctx.secrets` and is never returned.

## Creative ingestion

Three safe paths exist:

### Manual snippet import

Use supported Awin banner HTML for one publisher + advertiser.

Semantics: UPSERT_ONLY.

### Saved My Creative HTML

Save/export rendered My Creative HTML and import it offline.

The parser can group multiple advertisers.

Default semantics: UPSERT_ONLY.

Optional `completeAdvertiserId`: marks exactly that advertiser's supplied set as authoritative.

### Future authenticated source

Only add an authenticated complete-Creative source when Awin exposes a supported or safely testable surface. Do not guess undocumented private endpoints.

## Test

```bash
python -m pytest
```

Tests are designed to run without production credentials.
