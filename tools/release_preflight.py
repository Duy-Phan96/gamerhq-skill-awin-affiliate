from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

EXPECTED_PACKAGE_NAME = "gamerhq-skill-awin-affiliate"
EXPECTED_SKILL_ID = "awin-affiliate"
EXPECTED_ENTRY_POINT = "gamerhq_skill_awin_affiliate:create_skill"
EXPECTED_RUNTIME_API = "1"
CONTRACT_HEADING = re.compile(r"^## `([^`]+)`$", flags=re.MULTILINE)
STABLE_VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


@dataclass(frozen=True, slots=True)
class RuntimeIdentity:
    package_constant: str
    exported_manifest_version: str
    base_manifest_version: str
    exported_skill_id: str
    base_skill_id: str
    exported_runtime_api: str
    base_runtime_api: str
    permissions: tuple[str, ...]
    management_contract_ids: tuple[str, ...]


def load_runtime_identity() -> RuntimeIdentity:
    from gamerhq_skill_awin_affiliate import AwinAffiliateSkill, __version__
    from gamerhq_skill_awin_affiliate.skill import (
        AwinAffiliateSkill as BaseAwinAffiliateSkill,
    )

    exported = AwinAffiliateSkill.manifest
    base = BaseAwinAffiliateSkill.manifest
    return RuntimeIdentity(
        package_constant=__version__,
        exported_manifest_version=exported.version,
        base_manifest_version=base.version,
        exported_skill_id=exported.id,
        base_skill_id=base.id,
        exported_runtime_api=exported.runtime_api_version,
        base_runtime_api=base.runtime_api_version,
        permissions=tuple(exported.permissions),
        management_contract_ids=tuple(
            contract.id for contract in exported.management_apis.exposes
        ),
    )


def _read_text(root: Path, relative: str, errors: list[str]) -> str:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"Missing required file: {relative}")
        return ""


def _read_pyproject(root: Path, errors: list[str]) -> dict:
    path = root / "pyproject.toml"
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except FileNotFoundError:
        errors.append("Missing required file: pyproject.toml")
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"pyproject.toml is invalid TOML: {exc}")
    return {}


def _is_stable_one_x_or_newer(version: str) -> bool:
    match = STABLE_VERSION.fullmatch(version)
    return bool(match and int(match.group(1)) >= 1)


def collect_release_preflight_errors(
    root: Path,
    *,
    identity: RuntimeIdentity | None = None,
) -> tuple[str, ...]:
    root = root.resolve()
    errors: list[str] = []
    identity = identity or load_runtime_identity()
    pyproject = _read_pyproject(root, errors)

    project = pyproject.get("project") if isinstance(pyproject, dict) else None
    project = project if isinstance(project, dict) else {}
    tool = pyproject.get("tool") if isinstance(pyproject, dict) else None
    tool = tool if isinstance(tool, dict) else {}
    gamerhq = tool.get("gamerhq") if isinstance(tool, dict) else None
    gamerhq = gamerhq if isinstance(gamerhq, dict) else {}

    package_name = str(project.get("name", "")).strip()
    package_version = str(project.get("version", "")).strip()
    skill_id = str(gamerhq.get("skill-id", "")).strip()
    runtime_api = str(gamerhq.get("runtime-api", "")).strip()
    capabilities_raw = gamerhq.get("capabilities", ())
    capabilities = (
        tuple(str(value) for value in capabilities_raw)
        if isinstance(capabilities_raw, list)
        else ()
    )

    entry_points = project.get("entry-points")
    entry_points = entry_points if isinstance(entry_points, dict) else {}
    skill_entry_points = entry_points.get("gamerhq.skills")
    skill_entry_points = (
        skill_entry_points if isinstance(skill_entry_points, dict) else {}
    )
    entry_point = str(skill_entry_points.get(EXPECTED_SKILL_ID, "")).strip()

    if package_name != EXPECTED_PACKAGE_NAME:
        errors.append(
            f"Package name mismatch: expected {EXPECTED_PACKAGE_NAME!r}, got {package_name!r}."
        )
    if not package_version:
        errors.append("pyproject.toml project.version is missing.")

    versions = {
        "pyproject.toml": package_version,
        "package __version__": identity.package_constant,
        "exported Skill manifest": identity.exported_manifest_version,
        "base Skill manifest": identity.base_manifest_version,
    }
    if len(set(versions.values())) != 1:
        rendered = ", ".join(f"{name}={value!r}" for name, value in versions.items())
        errors.append(f"Version identity drift: {rendered}.")

    skill_ids = {
        "pyproject.toml": skill_id,
        "exported Skill manifest": identity.exported_skill_id,
        "base Skill manifest": identity.base_skill_id,
    }
    if set(skill_ids.values()) != {EXPECTED_SKILL_ID}:
        rendered = ", ".join(f"{name}={value!r}" for name, value in skill_ids.items())
        errors.append(f"Skill ID drift: {rendered}.")

    runtime_apis = {
        "pyproject.toml": runtime_api,
        "exported Skill manifest": identity.exported_runtime_api,
        "base Skill manifest": identity.base_runtime_api,
    }
    if set(runtime_apis.values()) != {EXPECTED_RUNTIME_API}:
        rendered = ", ".join(
            f"{name}={value!r}" for name, value in runtime_apis.items()
        )
        errors.append(f"Runtime API drift: {rendered}.")

    if entry_point != EXPECTED_ENTRY_POINT:
        errors.append(
            f"Entry point mismatch: expected {EXPECTED_ENTRY_POINT!r}, got {entry_point!r}."
        )

    if set(capabilities) != set(identity.permissions):
        errors.append(
            "Capability metadata drift: pyproject.toml and the executable Skill manifest differ."
        )

    readme = _read_text(root, "README.md", errors)
    if package_version and f"Current package version: **{package_version}**" not in readme:
        errors.append(
            f"README.md does not declare the current package version {package_version}."
        )

    changelog = _read_text(root, "CHANGELOG.md", errors)
    if "## [Unreleased]" not in changelog:
        errors.append("CHANGELOG.md is missing the [Unreleased] section.")
    if package_version and f"## [{package_version}]" not in changelog:
        errors.append(
            f"CHANGELOG.md is missing a section for package version {package_version}."
        )

    contract_doc = _read_text(root, "docs/management-api-contracts.md", errors)
    documented_contracts = tuple(CONTRACT_HEADING.findall(contract_doc))
    if len(documented_contracts) != len(set(documented_contracts)):
        errors.append("Management contract documentation contains duplicate contract headings.")
    if set(documented_contracts) != set(identity.management_contract_ids):
        missing = sorted(set(identity.management_contract_ids) - set(documented_contracts))
        extra = sorted(set(documented_contracts) - set(identity.management_contract_ids))
        errors.append(
            "Management contract documentation drift: "
            f"missing={missing or 'none'}, extra={extra or 'none'}."
        )

    if _is_stable_one_x_or_newer(package_version):
        if not (root / "LICENSE").is_file():
            errors.append("Stable 1.x release candidates require an approved LICENSE file.")
        if "BLOCKED BY LIVE ACCEPTANCE" in readme:
            errors.append(
                "Stable 1.x release candidates cannot retain the BLOCKED BY LIVE ACCEPTANCE state."
            )

    return tuple(errors)


def run_preflight(root: Path) -> tuple[str, ...]:
    return collect_release_preflight_errors(root)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Awin Affiliate release metadata and compatibility identity."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Defaults to the current working directory.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    errors = run_preflight(args.root)
    if errors:
        print("Release preflight FAILED:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    identity = load_runtime_identity()
    print(
        "Release preflight PASS: "
        f"skill={identity.exported_skill_id} "
        f"version={identity.exported_manifest_version} "
        f"runtime_api={identity.exported_runtime_api} "
        f"contracts={len(identity.management_contract_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
