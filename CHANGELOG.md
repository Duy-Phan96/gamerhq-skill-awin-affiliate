# Changelog

## 0.2.0

- Add secure Awin access-token validation through the public GamerHQ Skill Runtime.
- Discover publisher accounts through Awin and auto-select the only available publisher.
- Require explicit publisher selection when several publisher accounts are available.
- Store the access token only through encrypted `secrets.skill` storage.
- Expose safe connection status and disconnect Management APIs without returning credentials.
- Normalize authentication, rate-limit, provider-outage and transport failures.
- Keep the Skill independent from Recurring Posts and GamerHQ application internals.

## 0.1.0

- Add the standalone `awin-affiliate` Skill package.
- Add normalized Creative records and persistent `creatives.v1` library.
- Add isolated Awin HTML image-banner import with validation and deduplication.
- Add offline tests, portability checks and CI on Python 3.12 and 3.14.
