from pathlib import Path

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, create_skill
from skill_runtime import (
    require_clean_skill_source,
    validate_skill_factory,
    validate_skill_package_matches_implementation,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "gamerhq_skill_awin_affiliate"


def test_source_stays_portable():
    report = require_clean_skill_source((PACKAGE,))
    assert report.passed


def test_factory_matches_stable_skill_identity():
    report = validate_skill_factory(create_skill, expected_skill_id="awin-affiliate")
    assert report.skill_id == "awin-affiliate"
    assert report.version == "0.8.0"


def test_static_package_metadata_matches_manifest():
    report = validate_skill_package_matches_implementation(
        ROOT / "pyproject.toml",
        AwinAffiliateSkill(),
    )
    assert report.skill_id == "awin-affiliate"
    assert "storage.skill" in report.capabilities
    assert "scheduler.jobs" in report.capabilities
