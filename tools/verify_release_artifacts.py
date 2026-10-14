from __future__ import annotations

import argparse
import hashlib
import sys
import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import Sequence

EXPECTED_SKILL_ID = "awin-affiliate"
EXPECTED_RUNTIME_API = "1"
EXPECTED_AUTHOR = "Duy Phan"
EXPECTED_LICENSE = "MIT"
REQUIRED_WHEEL_MEMBERS = (
    "gamerhq_skill_awin_affiliate/__init__.py",
    "gamerhq_skill_awin_affiliate/_version.py",
    "gamerhq_skill_awin_affiliate/hardened_skill.py",
    "gamerhq_skill_awin_affiliate/skill.py",
)
REQUIRED_SDIST_MEMBERS = (
    "LICENSE",
    "pyproject.toml",
    "README.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "MANIFEST.in",
    "docs/management-api-contracts.md",
    "docs/live-acceptance.md",
    "docs/live-acceptance-report-template.md",
    "docs/release-process.md",
    "docs/release-checklist.md",
    "docs/legal-and-distribution.md",
    "gamerhq_skill_awin_affiliate/__init__.py",
    "gamerhq_skill_awin_affiliate/_version.py",
    "gamerhq_skill_awin_affiliate/hardened_skill.py",
    "tests/test_contract.py",
    "tests/test_release_preflight.py",
    "tests/test_license_distribution.py",
    "tools/live_acceptance_attestation.py",
    "tools/release_preflight.py",
    "tools/verify_release_artifacts.py",
)


def _project_identity(root: Path) -> tuple[str, str]:
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    return str(project["name"]), str(project["version"])


def _metadata_identity(text: str) -> tuple[str, str, str, str]:
    message = Parser().parsestr(text)
    license_name = str(
        message.get("License-Expression") or message.get("License") or ""
    ).strip()
    return (
        str(message.get("Name", "")).strip(),
        str(message.get("Version", "")).strip(),
        str(message.get("Author", "")).strip(),
        license_name,
    )


def _one(paths: list[Path], label: str, errors: list[str]) -> Path | None:
    if len(paths) != 1:
        errors.append(f"Expected exactly one {label}; found {len(paths)}.")
        return None
    return paths[0]


def _verify_metadata(
    metadata: str,
    *,
    label: str,
    package_name: str,
    version: str,
    errors: list[str],
) -> None:
    actual_name, actual_version, actual_author, actual_license = _metadata_identity(
        metadata
    )
    if actual_name != package_name or actual_version != version:
        errors.append(
            f"{label} metadata mismatch: "
            f"Name={actual_name!r}, Version={actual_version!r}."
        )
    if actual_author != EXPECTED_AUTHOR:
        errors.append(
            f"{label} author mismatch: expected {EXPECTED_AUTHOR!r}, got {actual_author!r}."
        )
    if actual_license != EXPECTED_LICENSE:
        errors.append(
            f"{label} license mismatch: expected {EXPECTED_LICENSE!r}, got {actual_license!r}."
        )


def _verify_wheel(
    wheel: Path,
    *,
    root: Path,
    package_name: str,
    version: str,
    errors: list[str],
) -> None:
    normalized = package_name.replace("-", "_")
    expected_name = f"{normalized}-{version}-py3-none-any.whl"
    if wheel.name != expected_name:
        errors.append(
            f"Wheel filename mismatch: expected {expected_name!r}, got {wheel.name!r}."
        )

    try:
        expected_license = (root / "LICENSE").read_bytes()
    except OSError as exc:
        errors.append(f"Repository LICENSE cannot be read: {exc}.")
        expected_license = b""

    try:
        with zipfile.ZipFile(wheel) as archive:
            members = set(archive.namelist())
            missing = sorted(set(REQUIRED_WHEEL_MEMBERS) - members)
            if missing:
                errors.append(f"Wheel is missing required members: {missing}.")

            metadata_files = [
                member for member in members if member.endswith(".dist-info/METADATA")
            ]
            if len(metadata_files) != 1:
                errors.append(
                    "Wheel must contain exactly one .dist-info/METADATA file."
                )
            else:
                metadata = archive.read(metadata_files[0]).decode("utf-8")
                _verify_metadata(
                    metadata,
                    label="Wheel",
                    package_name=package_name,
                    version=version,
                    errors=errors,
                )

            wheel_files = [
                member for member in members if member.endswith(".dist-info/WHEEL")
            ]
            if len(wheel_files) != 1:
                errors.append("Wheel must contain exactly one .dist-info/WHEEL file.")
            else:
                wheel_metadata = archive.read(wheel_files[0]).decode("utf-8")
                if "Tag: py3-none-any" not in wheel_metadata:
                    errors.append("Wheel is not tagged as py3-none-any.")

            license_files = [
                member
                for member in members
                if member.endswith(".dist-info/licenses/LICENSE")
            ]
            if len(license_files) != 1:
                errors.append(
                    "Wheel must contain exactly one .dist-info/licenses/LICENSE file."
                )
            elif expected_license and archive.read(license_files[0]) != expected_license:
                errors.append("Wheel LICENSE content differs from the repository LICENSE.")
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError) as exc:
        errors.append(f"Wheel cannot be inspected: {exc}.")


def _verify_sdist(
    sdist: Path,
    *,
    root: Path,
    package_name: str,
    version: str,
    errors: list[str],
) -> None:
    normalized = package_name.replace("-", "_")
    expected_name = f"{normalized}-{version}.tar.gz"
    if sdist.name != expected_name:
        errors.append(
            f"Source-distribution filename mismatch: expected {expected_name!r}, got {sdist.name!r}."
        )

    try:
        expected_license = (root / "LICENSE").read_bytes()
    except OSError as exc:
        errors.append(f"Repository LICENSE cannot be read: {exc}.")
        expected_license = b""

    try:
        with tarfile.open(sdist, mode="r:gz") as archive:
            names = archive.getnames()
            top_levels = {name.split("/", 1)[0] for name in names if name}
            if len(top_levels) != 1:
                errors.append(
                    f"Source distribution must have one top-level directory; got {sorted(top_levels)}."
                )
                return
            top_level = next(iter(top_levels))
            relative_members = {
                name[len(top_level) + 1 :]
                for name in names
                if name.startswith(f"{top_level}/")
            }
            missing = sorted(set(REQUIRED_SDIST_MEMBERS) - relative_members)
            if missing:
                errors.append(
                    f"Source distribution is missing required members: {missing}."
                )

            pkg_info_name = f"{top_level}/PKG-INFO"
            try:
                pkg_info_file = archive.extractfile(pkg_info_name)
            except KeyError:
                pkg_info_file = None
            if pkg_info_file is None:
                errors.append("Source distribution is missing PKG-INFO.")
            else:
                pkg_info = pkg_info_file.read().decode("utf-8")
                _verify_metadata(
                    pkg_info,
                    label="Source-distribution",
                    package_name=package_name,
                    version=version,
                    errors=errors,
                )

            license_name = f"{top_level}/LICENSE"
            try:
                license_file = archive.extractfile(license_name)
            except KeyError:
                license_file = None
            if license_file is None:
                errors.append("Source distribution is missing LICENSE.")
            elif expected_license and license_file.read() != expected_license:
                errors.append(
                    "Source-distribution LICENSE content differs from the repository LICENSE."
                )
    except (OSError, tarfile.TarError, UnicodeDecodeError) as exc:
        errors.append(f"Source distribution cannot be inspected: {exc}.")


def collect_artifact_errors(root: Path, dist: Path) -> tuple[str, ...]:
    root = root.resolve()
    dist = dist.resolve()
    errors: list[str] = []

    try:
        package_name, version = _project_identity(root)
    except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError) as exc:
        return (f"Cannot read project identity: {exc}.",)

    if not dist.is_dir():
        return (f"Artifact directory does not exist: {dist}.",)

    wheel = _one(sorted(dist.glob("*.whl")), "wheel", errors)
    sdist = _one(sorted(dist.glob("*.tar.gz")), "source distribution", errors)

    if wheel is not None:
        _verify_wheel(
            wheel,
            root=root,
            package_name=package_name,
            version=version,
            errors=errors,
        )
    if sdist is not None:
        _verify_sdist(
            sdist,
            root=root,
            package_name=package_name,
            version=version,
            errors=errors,
        )

    return tuple(errors)


def write_sha256sums(dist: Path) -> Path:
    artifacts = sorted(
        path
        for path in dist.iterdir()
        if path.is_file() and path.name != "SHA256SUMS.txt"
    )
    output = dist / "SHA256SUMS.txt"
    lines = []
    for artifact in artifacts:
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        lines.append(f"{digest}  {artifact.name}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect Awin Affiliate wheel/source release artifacts."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--write-checksums", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = args.root.resolve()
    dist = args.dist if args.dist.is_absolute() else root / args.dist
    errors = collect_artifact_errors(root, dist)
    if errors:
        print("Release artifact verification FAILED:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    checksum_file = write_sha256sums(dist) if args.write_checksums else None
    package_name, version = _project_identity(root)
    print(
        "Release artifact verification PASS: "
        f"package={package_name} version={version} "
        f"wheel=1 sdist=1 skill={EXPECTED_SKILL_ID} runtime_api={EXPECTED_RUNTIME_API}"
    )
    if checksum_file is not None:
        print(f"Checksums written to {checksum_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
