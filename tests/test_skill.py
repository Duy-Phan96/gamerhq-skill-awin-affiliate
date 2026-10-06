import asyncio

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, STORAGE_KEY


HTML = """
<!-- START ADVERTISER: Ugovaper from awin.com -->
<a rel="sponsored" href="https://www.awin1.com/cread.php?s=4902463&v=129591&q=615955&r=3095707">
  <img src="https://www.awin1.com/cshow.php?s=4902463&v=129591&q=615955&r=3095707">
</a>
<!-- END ADVERTISER: Ugovaper from awin.com -->
"""


class Storage:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value):
        self.values[key] = value

    async def delete(self, key):
        self.values.pop(key, None)


class Audit:
    def __init__(self):
        self.calls = []

    async def write(self, **kwargs):
        self.calls.append(kwargs)


class Context:
    def __init__(self):
        self.guild_id = 123
        self.storage = Storage()
        self.audit = Audit()


def test_import_persists_and_reimport_updates_without_duplication():
    async def run():
        ctx = Context()
        skill = AwinAffiliateSkill()

        first = await skill.import_html(ctx, html=HTML, now=100)
        second = await skill.import_html(ctx, html=HTML, now=200)
        creatives = await skill.list_creatives(ctx)

        assert first["added"] == 1
        assert first["updated"] == 0
        assert second["added"] == 0
        assert second["updated"] == 1
        assert len(creatives) == 1
        assert creatives[0].first_seen_at == 100
        assert creatives[0].last_seen_at == 200
        assert len(ctx.storage.values[STORAGE_KEY]) == 1
        assert ctx.audit.calls[-1]["action"] == "creatives.imported"

    asyncio.run(run())


def test_manifest_is_standalone_and_does_not_consume_other_skills():
    skill = AwinAffiliateSkill()
    assert skill.manifest.id == "awin-affiliate"
    assert skill.manifest.public_apis.consumes == ()
    assert "storage.skill" in skill.manifest.permissions
    assert "secrets.skill" in skill.manifest.permissions
    assert "http.external" in skill.manifest.permissions
