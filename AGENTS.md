# Awin Affiliate Skill repository instructions

This package is a portable GamerHQ Skill.

Follow the canonical GamerHQ Skill Developer Guide, Authoring Contract and Review Checklist.

Hard rules:

- Keep Skill ID `awin-affiliate` stable.
- Do not import Discord.py or GamerHQ bot/cogs/services/database/hosts/config.
- Use only public `skill_runtime` contracts for host capabilities.
- Do not depend on the Recurring Posts Skill or Amazon Affiliate Skill.
- Awin-specific scheduling, rotation and campaign state belong to this Skill.
- Keep credentials out of logs, fixtures, examples and repository history.
- Do not implement authenticated scraping until official Awin capabilities have been checked.
- Isolate every creative source behind a provider adapter.
- Manual HTML imports must never mark unmentioned creatives as missing.
- Keep tests offline and token-free.
- Preserve stable storage keys and management contract IDs across compatible releases.
