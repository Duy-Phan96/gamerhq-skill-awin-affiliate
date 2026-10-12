from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, __version__
from gamerhq_skill_awin_affiliate.skill import (
    AwinAffiliateSkill as BaseAwinAffiliateSkill,
)
from tools.release_preflight import (
    collect_release_preflight_errors,
    load_runtime_identity,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_preflight_files(target: Path) -> None:
    (target / "docs").mkdir(parents=True)
    for relative in ("pyproject.toml", "README.md", "CHANGELOG.md"):
        shutil.copy2(ROOT / relative, target / relative)
    shutil.copy2(
        ROOT / "docs" / "management-api-contracts.md",
        target / "docs" / "management-api-contracts.md",
    )


def test_repository_release_preflight_passes():
    assert collect_release_preflight_errors(ROOT) == ()


def test_base_exported_and_package_versions_are_identical():
    assert __version__ == "0.9.3"
    assert AwinAffiliateSkill.manifest.version == __version__
    assert BaseAwinAffiliateSkill.manifest.version == __version__


def test_release_preflight_detects_package_version_drift(tmp_path: Path):
    _copy_preflight_files(tmp_path)
    pyproject = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        pyproject.replace('version = "0.9.3"', 'version = "0.9.4"'),
        encoding="utf-8",
    )

    errors = collect_release_preflight_errors(
        tmp_path,
        identity=load_runtime_identity(),
    )

    assert any("Version identity drift" in error for error in errors)


def test_stable_release_requires_license_and_non_blocked_status(tmp_path: Path):
    _copy_preflight_files(tmp_path)
    pyproject = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        pyproject.replace('version = "0.9.3"', 'version = "1.0.0"'),
        encoding="utf-8",
    )

    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    readme = readme.replace(
        "Current package version: **0.9.3**",
        "Current package version: **1.0.0**",
    ).replace("BLOCKED BY LIVE ACCEPTANCE", "READY FOR RELEASE")
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")

    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        changelog.replace("## [0.9.3]", "## [1.0.0]\n\n## [0.9.3]", 1),
        encoding="utf-8",
    )

    identity = replace(
        load_runtime_identity(),
        package_constant="1.0.0",
        exported_manifest_version="1.0.0",
        base_manifest_version="1.0.0",
    )
    errors = collect_release_preflight_errors(tmp_path, identity=identity)

    assert "Stable 1.x release candidates require an approved LICENSE file." in errors
    assert not any("Version identity drift" in error for error in errors)


def test_stable_release_accepts_license_after_owner_decision(tmp_path: Path):
    _copy_preflight_files(tmp_path)
    pyproject = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        pyproject.replace('version = "0.9.3"', 'version = "1.0.0"'),
        encoding="utf-8",
    )

    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    (tmp_path / "README.md").write_text(
        readme.replace(
            "Current package version: **0.9.3**",
            "Current package version: **1.0.0**",
        ).replace("BLOCKED BY LIVE ACCEPTANCE", "READY FOR RELEASE"),
        encoding="utf-8",
    )
    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        changelog.replace("## [0.9.3]", "## [1.0.0]\n\n## [0.9.3]", 1),
        encoding="utf-8",
    )
    (tmp_path / "LICENSE").write_text("Approved license text\n", encoding="utf-8")

    identity = replace(
        load_runtime_identity(),
        package_constant="1.0.0",
        exported_manifest_version="1.0.0",
        base_manifest_version="1.0.0",
    )

    assert collect_release_preflight_errors(tmp_path, identity=identity) == ()
