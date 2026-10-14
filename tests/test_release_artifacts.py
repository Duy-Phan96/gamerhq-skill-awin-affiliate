from __future__ import annotations

import io
import shutil
import tarfile
import zipfile
from pathlib import Path

from tools.verify_release_artifacts import (
    REQUIRED_SDIST_MEMBERS,
    REQUIRED_WHEEL_MEMBERS,
    collect_artifact_errors,
    write_sha256sums,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "gamerhq-skill-awin-affiliate"
NORMALIZED_NAME = "gamerhq_skill_awin_affiliate"
VERSION = "0.9.3"
AUTHOR = "Duy Phan"
LICENSE_NAME = "MIT"
LICENSE_BYTES = (ROOT / "LICENSE").read_bytes()


def _write_wheel(
    dist: Path,
    *,
    metadata_version: str = VERSION,
    metadata_author: str = AUTHOR,
    metadata_license: str = LICENSE_NAME,
    omit: str | None = None,
) -> Path:
    path = dist / f"{NORMALIZED_NAME}-{VERSION}-py3-none-any.whl"
    dist_info = f"{NORMALIZED_NAME}-{VERSION}.dist-info"
    members = {
        **{member: b"# synthetic test member\n" for member in REQUIRED_WHEEL_MEMBERS},
        f"{dist_info}/METADATA": (
            f"Metadata-Version: 2.4\nName: {PACKAGE_NAME}\n"
            f"Version: {metadata_version}\nAuthor: {metadata_author}\n"
            f"License: {metadata_license}\n"
        ).encode(),
        f"{dist_info}/WHEEL": b"Wheel-Version: 1.0\nTag: py3-none-any\n",
        f"{dist_info}/licenses/LICENSE": LICENSE_BYTES,
    }
    if omit is not None:
        members.pop(omit, None)
    with zipfile.ZipFile(path, mode="w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return path


def _write_sdist(
    dist: Path,
    *,
    metadata_version: str = VERSION,
    metadata_author: str = AUTHOR,
    metadata_license: str = LICENSE_NAME,
    omit: str | None = None,
) -> Path:
    path = dist / f"{NORMALIZED_NAME}-{VERSION}.tar.gz"
    top = f"{NORMALIZED_NAME}-{VERSION}"
    members = {
        **{member: b"# synthetic test member\n" for member in REQUIRED_SDIST_MEMBERS},
        "PKG-INFO": (
            f"Metadata-Version: 2.4\nName: {PACKAGE_NAME}\n"
            f"Version: {metadata_version}\nAuthor: {metadata_author}\n"
            f"License: {metadata_license}\n"
        ).encode(),
    }
    members["LICENSE"] = LICENSE_BYTES
    if omit is not None:
        members.pop(omit, None)
    with tarfile.open(path, mode="w:gz") as archive:
        for relative, content in members.items():
            info = tarfile.TarInfo(name=f"{top}/{relative}")
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return path


def _artifact_root(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    dist = root / "dist"
    dist.mkdir(parents=True)
    shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
    shutil.copy2(ROOT / "LICENSE", root / "LICENSE")
    return root, dist


def test_synthetic_release_artifacts_pass_verification(tmp_path: Path):
    root, dist = _artifact_root(tmp_path)
    _write_wheel(dist)
    _write_sdist(dist)

    assert collect_artifact_errors(root, dist) == ()


def test_release_artifacts_reject_wrong_wheel_metadata(tmp_path: Path):
    root, dist = _artifact_root(tmp_path)
    _write_wheel(dist, metadata_version="0.9.2")
    _write_sdist(dist)

    errors = collect_artifact_errors(root, dist)

    assert any("Wheel metadata mismatch" in error for error in errors)


def test_release_artifacts_reject_wrong_legal_metadata(tmp_path: Path):
    root, dist = _artifact_root(tmp_path)
    _write_wheel(dist, metadata_author="GamerHQ", metadata_license="Apache-2.0")
    _write_sdist(dist, metadata_author="GamerHQ", metadata_license="Apache-2.0")

    errors = collect_artifact_errors(root, dist)

    assert any("Wheel author mismatch" in error for error in errors)
    assert any("Wheel license mismatch" in error for error in errors)
    assert any("Source-distribution author mismatch" in error for error in errors)
    assert any("Source-distribution license mismatch" in error for error in errors)


def test_release_artifacts_reject_missing_wheel_license(tmp_path: Path):
    root, dist = _artifact_root(tmp_path)
    dist_info = f"{NORMALIZED_NAME}-{VERSION}.dist-info"
    _write_wheel(dist, omit=f"{dist_info}/licenses/LICENSE")
    _write_sdist(dist)

    errors = collect_artifact_errors(root, dist)

    assert any("dist-info/licenses/LICENSE" in error for error in errors)


def test_release_artifacts_reject_missing_source_member(tmp_path: Path):
    root, dist = _artifact_root(tmp_path)
    _write_wheel(dist)
    _write_sdist(dist, omit="docs/release-process.md")

    errors = collect_artifact_errors(root, dist)

    assert any("docs/release-process.md" in error for error in errors)


def test_sdist_requires_completed_report_when_repository_has_one(tmp_path: Path):
    root, dist = _artifact_root(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "live-acceptance-report.md").write_text(
        "LIVE_ACCEPTANCE_STATUS=PASS\n",
        encoding="utf-8",
    )
    _write_wheel(dist)
    _write_sdist(dist)

    errors = collect_artifact_errors(root, dist)

    assert any("docs/live-acceptance-report.md" in error for error in errors)


def test_checksum_file_covers_wheel_and_sdist(tmp_path: Path):
    root, dist = _artifact_root(tmp_path)
    wheel = _write_wheel(dist)
    sdist = _write_sdist(dist)

    checksum_file = write_sha256sums(dist)
    lines = checksum_file.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert any(line.endswith(f"  {wheel.name}") for line in lines)
    assert any(line.endswith(f"  {sdist.name}") for line in lines)
    assert all(len(line.split()[0]) == 64 for line in lines)
