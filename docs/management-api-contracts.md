# Management API contracts

Status: **1.0 compatibility candidate**

Package baseline: `gamerhq-skill-awin-affiliate` 0.9.3

Runtime API: `1`

This document is the host-neutral contract reference for the public Management APIs exposed by the standalone `awin-affiliate` Skill.

A compatible host calls these contracts through the GamerHQ Skill Runtime Management API boundary. It must not import implementation classes from this package.

## General conventions

### Payloads

- Requests and responses are JSON-compatible mappings.
- Unknown fields should not be relied upon as a compatibility mechanism.
- Identifiers are strings unless a field is explicitly documented as an integer.
- Timestamps are Unix seconds.
- Boolean fields require actual JSON booleans; strings such as `"false"` are invalid.
- Validation errors fail before a documented side effect whenever practical.

### Errors

Management handlers raise safe validation/provider/runtime errors through the host boundary. Error strings are intended to be understandable but are not stable machine identifiers.

Hosts should:

- render a safe generic failure message;
- never expose raw HTTP headers, credentials or private exceptions;
- retry only when the operation is known to be idempotent;
- re-read state after a failed mutating operation.

### Security

- The raw Awin access token is accepted only by `setup.connect.v1`.
- The token is stored through `secrets.skill`, never ordinary Skill storage.
- Diagnostics never includes the raw token or the masked setup marker.
- Outbound Creative image/tracking URLs must use HTTPS.
- Post confirmation must forward the returned `confirmPayload` rather than reconstructing a selection.

### Compatibility

All contract IDs in this document end in `.v1`. Their documented meanings are the proposed stable 1.0 baseline.

Adding optional response fields may be backward compatible. Removing/renaming required fields or changing their meaning requires a new versioned contract ID.

# Setup

## `awin-affiliate.setup.status.v1`

Read the stored connection and publisher-selection status.

**Request**

```json
{}
```

**Response**

```json
{
  "setup": {
    "connected": true,
    "publisherSelected": true,
    "publisher": {
      "id": "3095707",
      "name": "Example Publisher"
    },
    "token": "••••••••"
  }
}
```

When disconnected, `publisher` and `token` are `null`.

`token` is a compatibility-only masked marker. Hosts should use `connected` and should not display or persist the marker.

**Side effects:** none.

---

## `awin-affiliate.setup.connect.v1`

Verify an Awin user access token, store it securely and discover publisher accounts.

**Request**

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `accessToken` | string | yes | Raw Awin user access token. |

```json
{
  "accessToken": "<secret>"
}
```

**Response — one account / auto-selected**

```json
{
  "setup": {
    "connected": true,
    "selectionRequired": false,
    "accounts": [
      {
        "id": "3095707",
        "name": "Example Publisher",
        "type": "publisher",
        "userRole": "admin"
      }
    ],
    "publisher": {
      "id": "3095707",
      "name": "Example Publisher"
    }
  }
}
```

With multiple accounts, `selectionRequired` is `true` unless the previous selected publisher remains available; `publisher` may be `null`.

**Validation and safety**

- Empty tokens are rejected.
- The token is verified through Awin before replacing the stored credential.
- A token with no accessible publisher account is rejected.
- The raw token is never returned or written to audit metadata.

**Side effects**

- stores the verified token in the Skill secret store;
- stores or clears the publisher selection in `settings.v1`;
- writes a safe audit event.

---

## `awin-affiliate.setup.accounts.v1`

List publisher accounts available to the currently connected Awin user.

**Request**

```json
{}
```

**Response**

```json
{
  "accounts": [
    {
      "id": "3095707",
      "name": "Example Publisher",
      "type": "publisher",
      "userRole": "admin"
    }
  ]
}
```

**Validation:** an Awin account must already be connected.

**Side effects:** external Awin API read only.

---

## `awin-affiliate.setup.select-publisher.v1`

Select one publisher account from the accounts available to the connected Awin user.

**Request**

```json
{
  "publisherId": "3095707"
}
```

**Response**

```json
{
  "publisher": {
    "id": "3095707",
    "name": "Example Publisher"
  }
}
```

**Validation**

- `publisherId` is required.
- The ID must exist in a fresh account listing for the connected token.

**Side effects**

- updates `settings.v1`;
- writes a safe audit event.

---

## `awin-affiliate.setup.disconnect.v1`

Delete the stored Awin token and clear publisher selection.

**Request**

```json
{}
```

**Response**

```json
{
  "disconnected": true
}
```

**Side effects**

- deletes `awin-access-token.v1` from encrypted Skill secrets;
- clears publisher selection in `settings.v1`;
- preserves Creatives, post state, campaigns and history;
- writes a safe audit event.

# Advertisers

## `awin-affiliate.advertisers.list.v1`

List Awin programmes/advertisers for the selected publisher.

**Request**

| Field | Type | Required | Values |
|---|---|---:|---|
| `relationship` | string or null | no | `joined`, `pending`, `suspended`, `rejected`, `notjoined` |

```json
{
  "relationship": "joined"
}
```

**Response**

```json
{
  "advertisers": [
    {
      "id": "129591",
      "name": "Example Advertiser",
      "relationship": "joined",
      "status": "active",
      "logoUrl": "https://example.invalid/logo.png",
      "description": "Example programme",
      "countryCode": "DE",
      "currencyCode": "EUR",
      "clickThroughUrl": "https://example.invalid"
    }
  ]
}
```

Nullable provider fields may be `null`.

**Validation:** connected token and selected publisher are required; unsupported relationship values are rejected.

**Side effects:** external Awin API read only.

# Creative Library

## `awin-affiliate.creatives.list.v1`

List and filter the persisted Creative Library.

**Request**

| Field | Type | Required | Default / constraint |
|---|---|---:|---|
| `advertiserId` | string | no | all advertisers |
| `type` | string | no | all types |
| `enabledOnly` | boolean | no | `false` |
| `activeOnly` | boolean | no | `false`; eligible states are `ACTIVE` and `NEW` |
| `offset` | integer | no | `0`, minimum `0` |
| `limit` | integer | no | `25`, range `1..25` |

**Response**

```json
{
  "creatives": {
    "items": [
      {
        "id": "awin:3095707:129591:101",
        "advertiserId": "129591",
        "advertiserName": "Example Advertiser",
        "type": "image",
        "title": "Example banner",
        "dimensions": "300×250",
        "imageUrl": "https://www.awin1.com/cshow.php?...",
        "trackingUrl": "https://www.awin1.com/cread.php?...",
        "state": "ACTIVE",
        "userEnabled": true,
        "source": "saved_my_creative_html",
        "lastSeenAt": 1791450000,
        "lastSyncedAt": 1791450000
      }
    ],
    "total": 1,
    "offset": 0,
    "limit": 25,
    "hasPrevious": false,
    "hasNext": false
  }
}
```

`dimensions`, names, timestamps and title may be `null`.

**Side effects:** none.

---

## `awin-affiliate.creatives.get.v1`

Read one Creative by stable Creative ID.

**Request**

```json
{
  "creativeId": "awin:3095707:129591:101"
}
```

**Response**

```json
{
  "creative": {
    "id": "awin:3095707:129591:101",
    "advertiserId": "129591",
    "advertiserName": "Example Advertiser",
    "type": "image",
    "title": "Example banner",
    "dimensions": "300×250",
    "imageUrl": "https://www.awin1.com/cshow.php?...",
    "trackingUrl": "https://www.awin1.com/cread.php?...",
    "state": "ACTIVE",
    "userEnabled": true,
    "source": "saved_my_creative_html",
    "lastSeenAt": 1791450000,
    "lastSyncedAt": 1791450000
  }
}
```

**Validation:** `creativeId` is required and must exist.

**Side effects:** none.

---

## `awin-affiliate.creatives.preview.v1`

Build a host-neutral Discord preview model for one Creative.

**Request**

```json
{
  "creativeId": "awin:3095707:129591:101"
}
```

**Response**

```json
{
  "creative": {
    "id": "awin:3095707:129591:101",
    "state": "ACTIVE",
    "userEnabled": true
  },
  "discordPreview": {
    "title": "Example Advertiser",
    "imageUrl": "https://www.awin1.com/cshow.php?...",
    "button": {
      "label": "View offer",
      "url": "https://www.awin1.com/cread.php?..."
    },
    "disclosure": "Werbung · Affiliate-Link",
    "supportingText": "Mit Nutzung des Links unterstützt ihr den Server."
  }
}
```

The actual `creative` object uses the complete management-view shape documented by `creatives.get.v1`.

**Side effects:** none.

---

## `awin-affiliate.creatives.set-enabled.v1`

Enable or disable one or more Creatives.

**Request**

Accepted selection forms:

```json
{
  "creativeIds": ["creative-a", "creative-b"],
  "enabled": false
}
```

```json
{
  "creativeId": "creative-a",
  "enabled": true
}
```

`creativeIds` may also be one string. At least one ID is required; maximum 100 unique IDs.

**Response**

```json
{
  "updated": 2,
  "changed": 1,
  "enabled": false
}
```

`updated` is the number of requested IDs; `changed` is the number whose stored value changed.

**Validation:** all requested IDs must exist; otherwise no partial write is performed.

**Side effects:** updates `creatives.v1` and writes a safe audit event.

---

## `awin-affiliate.creatives.set-advertiser-enabled.v1`

Enable or disable all matching Creatives for one advertiser.

**Request**

```json
{
  "advertiserId": "129591",
  "enabled": false,
  "activeOnly": true
}
```

`activeOnly` defaults to `false`.

**Response**

```json
{
  "updated": 4,
  "changed": 3,
  "enabled": false
}
```

A selection with no matching Creatives returns zero counts.

**Side effects:** updates `creatives.v1` and writes a safe audit event when matches exist.

---

## `awin-affiliate.creatives.import-html.v1`

Import one publisher/advertiser scope from supported Awin image-banner HTML.

**Request**

```json
{
  "html": "<a href=\"https://www.awin1.com/cread.php?...\"><img src=\"https://www.awin1.com/cshow.php?...\"></a>",
  "advertiserName": "Optional display override"
}
```

**Response**

```json
{
  "import": {
    "source": "manual_html",
    "publisherId": "3095707",
    "advertiserId": "129591",
    "found": 1,
    "new": 1,
    "updated": 0,
    "missing": 0,
    "restored": 0,
    "unchanged": 0,
    "total": 1,
    "added": 1,
    "creativeIds": ["awin:3095707:129591:101"]
  }
}
```

**Validation and authority**

- HTML is required.
- Tracking/image URLs must be supported HTTPS Awin URLs without URL credentials.
- Required Awin query IDs must be present.
- One manual import must contain exactly one publisher and advertiser scope.
- Manual imports are always `UPSERT_ONLY`; omitted Creatives never become `MISSING`.

**Side effects:** synchronizes `creatives.v1` and writes safe audit events.

---

## `awin-affiliate.creatives.import-saved-html.v1`

Import one or more publisher/advertiser groups from a saved My Creative HTML page.

**Request — safe default**

```json
{
  "html": "<html>...</html>"
}
```

**Request — explicitly authoritative for one advertiser**

```json
{
  "html": "<html>...</html>",
  "completeAdvertiserId": "129591"
}
```

A host must request explicit administrator confirmation before sending `completeAdvertiserId`.

**Response**

```json
{
  "import": {
    "groups": 2,
    "found": 6,
    "new": 2,
    "updated": 1,
    "missing": 1,
    "restored": 0,
    "unchanged": 3,
    "authoritativeAdvertiserId": "129591",
    "groupResults": [
      {
        "source": "saved_my_creative_html",
        "publisherId": "3095707",
        "advertiserId": "129591",
        "found": 4,
        "new": 1,
        "updated": 1,
        "missing": 1,
        "restored": 0,
        "unchanged": 2,
        "total": 5
      }
    ]
  }
}
```

`groups` is always the numeric count. Detailed rows are always in `groupResults`.

**Authority**

- Every group is `UPSERT_ONLY` by default.
- Only the group matching the explicit `completeAdvertiserId` becomes authoritative.
- Other advertiser groups in the same HTML remain `UPSERT_ONLY`.
- An unknown `completeAdvertiserId` is rejected before synchronization.

**Side effects:** synchronizes `creatives.v1` and writes safe aggregate audit metadata; raw HTML is not audited.

# Post Now

## `awin-affiliate.post.preview.v1`

Resolve one exact eligible Creative and build a Discord post preview without sending it.

**Request**

| Field | Type | Required | Notes |
|---|---|---:|---|
| `channelId` | integer | yes | Must resolve to a text channel or thread. |
| `selectionMode` | string | no | `specific` (default), `random`, `next` |
| `creativeId` | string | for `specific` | Stable Creative ID. |
| `advertiserId` | string | for `random`/`next` | Selection is advertiser-scoped. |
| `title` | string or null | no | Maximum 256 characters. |
| `text` | string or null | no | Maximum 2000 characters. |

**Response**

```json
{
  "preview": {
    "channelId": 50,
    "selection": {
      "creativeId": "awin:3095707:129591:101",
      "advertiserId": "129591",
      "mode": "specific"
    },
    "content": "**Werbung · Affiliate-Link**\nMit Nutzung des Links unterstützt ihr den Server.",
    "embed": {
      "title": "Example offer",
      "image": {"url": "https://www.awin1.com/cshow.php?..."}
    },
    "linkButtons": [
      {
        "label": "View offer",
        "url": "https://www.awin1.com/cread.php?..."
      }
    ]
  },
  "confirmPayload": {
    "channelId": 50,
    "creativeId": "awin:3095707:129591:101",
    "selectionMode": "specific",
    "title": "Example offer",
    "text": null
  }
}
```

Tuples produced by Python are serialized as JSON arrays by the host boundary.

**Critical compatibility rule:** a host must retain and forward `confirmPayload` unchanged to `post.send.v1`. It must not re-run random/next selection or reconstruct the Creative.

**Side effects:** none.

---

## `awin-affiliate.post.send.v1`

Revalidate and send the exact Creative resolved by `post.preview.v1`.

**Request**

Use the exact `confirmPayload` returned by preview.

```json
{
  "channelId": 50,
  "creativeId": "awin:3095707:129591:101",
  "selectionMode": "specific",
  "title": "Example offer",
  "text": null
}
```

**Response**

```json
{
  "sent": true,
  "messageId": 9001,
  "channelId": 50,
  "creativeId": "awin:3095707:129591:101",
  "advertiserId": "129591"
}
```

**Revalidation**

- channel must still be a text channel/thread;
- Creative must still exist, be enabled and have state `ACTIVE` or `NEW`;
- image/tracking URLs must still be valid HTTPS URLs.

**Side effects**

- sends one Discord message;
- updates advertiser-scoped `post-state.v1` only after successful send;
- writes a safe audit event.

# Campaigns

## `awin-affiliate.campaigns.list.v1`

List all persisted Awin campaigns with status derived from current Creative eligibility.

**Request**

```json
{}
```

**Response**

```json
{
  "campaigns": [
    {
      "id": "campaign-id",
      "name": "Daily deals",
      "advertiserId": "129591",
      "channelId": 50,
      "selectedCreativeIds": ["creative-a", "creative-b"],
      "rotation": "sequential",
      "intervalSeconds": 10800,
      "enabled": true,
      "avoidImmediateRepeat": true,
      "lastCreativeId": "creative-a",
      "sequentialIndex": 1,
      "shuffleRemaining": [],
      "blockedReason": null,
      "eligibleCreativeCount": 2,
      "configuredCreativeCount": 2,
      "status": "active"
    }
  ]
}
```

`status` is `active`, `paused` or `blocked`. A currently ineligible enabled campaign is reported as blocked even if the persisted diagnostic reason has not yet been updated by a run.

**Side effects:** none.

---

## `awin-affiliate.campaigns.get.v1`

Read one campaign using the same derived status/count shape as `campaigns.list.v1`.

**Request**

```json
{
  "campaignId": "campaign-id"
}
```

**Response**

```json
{
  "campaign": {
    "id": "campaign-id",
    "status": "active",
    "eligibleCreativeCount": 2,
    "configuredCreativeCount": 2
  }
}
```

The actual `campaign` object contains the complete campaign shape documented by `campaigns.list.v1`.

**Side effects:** none.

---

## `awin-affiliate.campaigns.create.v1`

Create and schedule one standalone Awin campaign.

**Request**

| Field | Type | Required | Notes |
|---|---|---:|---|
| `name` | string | yes | 1..80 characters |
| `advertiserId` | string | yes | Must match all selected Creatives |
| `channelId` | integer | yes | Text channel/thread |
| `selectedCreativeIds` | string or array of strings | yes | At least one existing Creative |
| `rotation` | string | no | `shuffle` default; `fixed`, `sequential`, `random`, `shuffle` |
| `intervalSeconds` | integer | yes | Minimum 900 seconds |
| `enabled` | boolean | no | `true` |
| `avoidImmediateRepeat` | boolean | no | `true` |

`fixed` requires exactly one selected Creative.

**Response**

```json
{
  "campaign": {
    "id": "generated-stable-id",
    "name": "Daily deals",
    "status": "active",
    "eligibleCreativeCount": 2,
    "configuredCreativeCount": 2
  }
}
```

The actual campaign uses the complete derived campaign shape.

**Side effects**

- writes `campaigns.v1`;
- creates/updates one Runtime scheduler job `campaign:<campaign-id>` when enabled;
- rolls back the newly persisted campaign on scheduler failure where practical;
- writes a safe audit event.

---

## `awin-affiliate.campaigns.update.v1`

Edit an existing campaign without changing its stable campaign ID or enabled state.

**Request**

`campaignId` is required. Other fields are optional and default to current values:

```json
{
  "campaignId": "campaign-id",
  "name": "Evening deals",
  "advertiserId": "129591",
  "channelId": 51,
  "selectedCreativeIds": ["creative-b"],
  "rotation": "fixed",
  "intervalSeconds": 7200,
  "avoidImmediateRepeat": false
}
```

Changing advertiser, Creative selection or rotation resets rotation state. Name/channel/interval-only changes preserve rotation progress.

**Response**

```json
{
  "campaign": {
    "id": "campaign-id",
    "name": "Evening deals",
    "status": "active"
  }
}
```

**Concurrency:** update is serialized against execution/pause/delete for the same campaign.

**Side effects:** updates `campaigns.v1`, updates the scheduler job and writes a safe audit event. Persisted state is compensated on scheduler failure where practical.

---

## `awin-affiliate.campaigns.set-active.v1`

Pause or resume one campaign.

**Request**

```json
{
  "campaignId": "campaign-id",
  "active": false
}
```

**Response**

```json
{
  "campaign": {
    "id": "campaign-id",
    "enabled": false,
    "status": "paused"
  }
}
```

**Concurrency:** serialized against an in-flight run/update/delete for the same campaign.

**Side effects**

- updates `campaigns.v1`;
- pause removes the scheduler job;
- resume upserts the scheduler job;
- persisted state is compensated on scheduler failure where practical.

---

## `awin-affiliate.campaigns.delete.v1`

Delete one campaign and its scheduler job.

**Request**

```json
{
  "campaignId": "campaign-id"
}
```

**Response**

```json
{
  "deleted": true,
  "campaignId": "campaign-id"
}
```

**Concurrency:** serialized against an in-flight run/update/pause for the same campaign.

**Side effects**

- removes the campaign from `campaigns.v1`;
- removes `campaign:<campaign-id>` from the Runtime scheduler;
- preserves retained history;
- restores persisted campaign state when scheduler removal fails where practical;
- writes a safe audit event.

---

## `awin-affiliate.campaigns.run-now.v1`

Execute one campaign immediately.

**Request**

```json
{
  "campaignId": "campaign-id"
}
```

A manual Run Now is allowed even when scheduled execution is paused; pause controls the recurring scheduler job.

**Success response**

```json
{
  "sent": true,
  "blocked": false,
  "messageId": 9002,
  "creativeId": "creative-a",
  "campaignId": "campaign-id"
}
```

**Blocked response**

```json
{
  "sent": false,
  "blocked": true,
  "reason": "No enabled active Creative is available."
}
```

**Concurrency and side effects**

- serialized against another execution or management mutation for the same campaign;
- different campaigns may send concurrently;
- aggregate state/history commits are serialized per guild;
- rotation advances only after successful Discord send;
- safe sent/blocked/failed history is appended;
- writes a safe audit event.

---

## `awin-affiliate.campaigns.preview-next.v1`

Preview the next eligible Creative without sending or mutating persisted rotation.

**Request**

```json
{
  "campaignId": "campaign-id"
}
```

**Success response**

```json
{
  "campaignId": "campaign-id",
  "blocked": false,
  "preview": {
    "creativeId": "creative-a",
    "advertiserId": "129591",
    "content": "**Werbung · Affiliate-Link**\nMit Nutzung des Links unterstützt ihr den Server.",
    "embed": {
      "title": "Example Advertiser",
      "image": {"url": "https://www.awin1.com/cshow.php?..."}
    },
    "linkButtons": [
      {
        "label": "View offer",
        "url": "https://www.awin1.com/cread.php?..."
      }
    ]
  },
  "rotationMutationApplied": false
}
```

**Blocked response**

```json
{
  "campaignId": "campaign-id",
  "blocked": true,
  "reason": "No enabled active Creative is available.",
  "preview": null
}
```

**Side effects:** none.

---

## `awin-affiliate.campaigns.history.v1`

Read recent retained delivery outcomes for one existing campaign.

**Request**

```json
{
  "campaignId": "campaign-id",
  "limit": 25
}
```

`limit` defaults to 25 and must be in `1..100`.

**Response**

```json
{
  "campaignId": "campaign-id",
  "history": [
    {
      "campaignId": "campaign-id",
      "outcome": "sent",
      "occurredAt": 1791450000,
      "creativeId": "creative-a",
      "channelId": 50,
      "messageId": 9002,
      "reason": null
    }
  ]
}
```

Rows are newest first. Outcomes are `sent`, `blocked` or `failed`. Reasons are safe generic values, never raw provider/Discord exception text.

History is globally bounded to the latest 100 retained campaign outcomes per guild.

**Side effects:** none.

# Diagnostics and discovery

## `awin-affiliate.diagnostics.v1`

Read safe aggregate operational diagnostics.

**Request**

```json
{}
```

**Response**

```json
{
  "diagnostics": {
    "setup": {
      "connected": true,
      "publisherSelected": true,
      "publisher": {
        "id": "3095707",
        "name": "Example Publisher"
      },
      "tokenStored": true
    },
    "creatives": {
      "total": 10,
      "enabled": 8,
      "disabled": 2,
      "byState": {
        "ACTIVE": 7,
        "MISSING": 2,
        "NEW": 1
      }
    },
    "campaigns": {
      "total": 3,
      "active": 1,
      "paused": 1,
      "blocked": 1
    },
    "deliveryHistory": {
      "retained": 20,
      "sent": 17,
      "blocked": 2,
      "failed": 1
    }
  }
}
```

**Security guarantees**

- no raw Awin token;
- no masked token marker;
- no Authorization header;
- no raw provider/Discord exception text;
- no network request is made to Awin for diagnostics.

**Side effects:** none.

---

## `awin-affiliate.describe.v1`

Describe the Skill boundary, available Creative sources and known limitations.

**Request**

```json
{}
```

**Response**

```json
{
  "skillId": "awin-affiliate",
  "standalone": true,
  "requiresRecurringPosts": false,
  "availableSources": [
    {
      "id": "manual_html",
      "label": "Awin HTML",
      "networkRequired": false,
      "credentialsRequired": false,
      "supportsMissingDetection": false
    },
    {
      "id": "saved_my_creative_html",
      "label": "Saved My Creative HTML",
      "networkRequired": false,
      "credentialsRequired": false,
      "supportsMultipleAdvertisers": true,
      "supportsMissingDetection": true,
      "missingDetectionRequiresExplicitCompleteAdvertiser": true
    },
    {
      "id": "awin_api",
      "label": "Awin Publisher API",
      "networkRequired": true,
      "credentialsRequired": true,
      "supportsAccountDiscovery": true,
      "supportsAdvertiserDiscovery": true,
      "supportsMissingDetection": false
    }
  ],
  "limitations": [
    "A complete official image-creative library endpoint has not been established yet.",
    "Manual imports do not mark omitted creatives as missing because a pasted snippet may be incomplete."
  ]
}
```

**Side effects:** none.

# Stable non-Management identities

These identities are part of the proposed 1.0 compatibility baseline but are not Management API IDs:

| Type | Identity |
|---|---|
| Skill ID | `awin-affiliate` |
| Runtime API | `1` |
| Settings storage | `settings.v1` |
| Creative storage | `creatives.v1` |
| Post-state storage | `post-state.v1` |
| Campaign storage | `campaigns.v1` |
| History storage | `campaign-history.v1` |
| Secret key | `awin-access-token.v1` |
| Scheduler handler | `awin-affiliate.campaign.execute.v1` |
| Scheduler job key | `campaign:<campaign-id>` |

# Host implementation guidance

A downstream host should:

1. discover the Skill through its package entry point;
2. read the manifest rather than hardcoding capabilities;
3. call only the public Management contracts listed above;
4. never store the raw Awin token itself;
5. forward Post Now `confirmPayload` unchanged;
6. request explicit confirmation before using `completeAdvertiserId`;
7. treat safe error text as human-facing, not as a stable error code;
8. avoid reading or mutating Skill storage directly;
9. keep its own integration/release/deployment lifecycle independent from this repository.
