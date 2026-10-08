# Awin API integration

## Authentication

Awin publisher APIs use a user-level access token. The Skill sends it as:

```text
Authorization: Bearer <token>
```

The raw token is stored only through `ctx.secrets` under:

```text
awin-access-token.v1
```

It must never be returned by Management APIs, written to normal Skill Storage, or included in audit metadata.

## Account discovery

The setup flow calls:

```text
GET https://api.awin.com/accounts?type=publisher
```

If exactly one publisher account is available, it is selected automatically.

If multiple publisher accounts are available, the Skill stores the verified token and asks the administrator to choose one by display name. The Management API still uses the stable account ID internally.

Publisher selection is persisted in `settings.v1`.

## Advertiser discovery

After publisher selection:

```text
GET https://api.awin.com/publishers/{publisherId}/programmes
```

Supported relationship filters:

- joined
- pending
- suspended
- rejected
- notjoined

The Skill normalizes returned programme metadata but does not currently treat this call as an authoritative Creative Library sync.

## Rate limit

Awin documents a general API throttling limit of 20 calls per minute per user. Interactive setup and advertiser discovery should therefore avoid unnecessary repeated calls.

## Creative limitation

The current official publisher API documentation exposes accounts, programmes, offers, deeplink/reporting and product-feed capabilities, but this implementation does not yet rely on an official endpoint for the complete image-banner Creative Library.

The `CreativeSource` boundary remains intentionally separate so a future supported source can replace or complement the manual HTML fallback without changing the Creative domain model.


## Saved My Creative HTML fallback

Awin's documented My Creative experience remains a platform tool rather than a complete Publisher API Creative-library endpoint used by this Skill.

The Skill therefore supports an offline saved-page fallback:

- save/export the rendered My Creative HTML;
- import the HTML without sharing an Awin browser session with the Skill;
- Awin tracking/image URLs are normalized into the same Creative model;
- multiple advertisers may be discovered from one saved page;
- every advertiser is UPSERT_ONLY by default;
- optional `completeAdvertiserId` makes only that advertiser authoritative after explicit administrator confirmation.

This fallback does not automate login and does not depend on undocumented private Awin endpoints.


## 1.0 provider-surface revalidation — 2026-10-08

The official Awin publisher help material was rechecked before 1.0 preparation.

Current documented state:

- My Creative remains the publisher platform area for banners, HTML links and other advertiser-provided media.
- Awin's Publisher API documentation continues to describe program data, commissions, transaction details, aggregate reporting and related publisher automation.
- This repository still does not rely on a documented Publisher API endpoint for the complete My Creative banner library.

Decision for 1.0:

- keep official Publisher API usage for account/programme discovery;
- keep manual/saved My Creative HTML as the banner-library fallback;
- do not add an authenticated browser-session scraper or guessed private endpoint;
- reconsider only if Awin publishes a supported/safely testable Creative-library surface.
