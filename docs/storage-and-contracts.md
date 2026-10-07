# Storage and public contracts

## Stable storage keys

### `settings.v1`

Publisher selection.

Does not contain the Awin token.

### `creatives.v1`

Normalized Creative Library.

Includes provider IDs, source, Creative state, user-enabled state and seen/sync timestamps.

### `post-state.v1`

Minimal per-advertiser last-Creative state used by Next selection.

### `campaigns.v1`

Standalone Awin campaign configuration and rotation state.

### `campaign-history.v1`

Bounded recent campaign outcomes.

Maximum retained entries: 100.

## Secret key

### `awin-access-token.v1`

Stored only through the encrypted Skill secret-store capability.

It is not part of ordinary Skill Storage.

## Scheduler handler

```text
awin-affiliate.campaign.execute.v1
```

Job keys:

```text
campaign:<campaign-id>
```

The Skill does not run a private scheduler loop.

## Management APIs

### Setup

- `awin-affiliate.setup.status.v1`
- `awin-affiliate.setup.connect.v1`
- `awin-affiliate.setup.accounts.v1`
- `awin-affiliate.setup.select-publisher.v1`
- `awin-affiliate.setup.disconnect.v1`

### Advertisers

- `awin-affiliate.advertisers.list.v1`

### Creative Library

- `awin-affiliate.creatives.list.v1`
- `awin-affiliate.creatives.get.v1`
- `awin-affiliate.creatives.preview.v1`
- `awin-affiliate.creatives.set-enabled.v1`
- `awin-affiliate.creatives.set-advertiser-enabled.v1`
- `awin-affiliate.creatives.import-html.v1`
- `awin-affiliate.creatives.import-saved-html.v1`

### Post Now

- `awin-affiliate.post.preview.v1`
- `awin-affiliate.post.send.v1`

### Campaigns

- `awin-affiliate.campaigns.list.v1`
- `awin-affiliate.campaigns.get.v1`
- `awin-affiliate.campaigns.create.v1`
- `awin-affiliate.campaigns.update.v1`
- `awin-affiliate.campaigns.set-active.v1`
- `awin-affiliate.campaigns.delete.v1`
- `awin-affiliate.campaigns.run-now.v1`
- `awin-affiliate.campaigns.preview-next.v1`
- `awin-affiliate.campaigns.history.v1`

### Diagnostics

- `awin-affiliate.diagnostics.v1`
- `awin-affiliate.describe.v1`

## Cross-Skill boundary

The Skill consumes no private implementation from another Skill.

In particular, recurring Awin campaigns do not depend on the Recurring Posts Skill.

Future cross-Skill communication, if added, must use documented Events or Public Skill APIs.
