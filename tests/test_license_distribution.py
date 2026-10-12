from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repository_license_and_author_identity_match_owner_decision():
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    assert project["license"] == {"text": "MIT"}
    assert project["authors"] == [{"name": "Duy Phan"}]

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("MIT License\n")
    assert "Copyright (c) 2026 Duy Phan" in license_text
    assert "Permission is hereby granted, free of charge" in license_text
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in license_text


def test_initial_distribution_is_github_release_only():
    decision = (ROOT / "docs" / "legal-and-distribution.md").read_text(
        encoding="utf-8"
    )
    release_process = (ROOT / "docs" / "release-process.md").read_text(
        encoding="utf-8"
    )

    assert "GitHub Release only" in decision
    assert "PyPI is deliberately deferred" in decision
    assert "does not authorize, schedule or imply" in decision
    assert "GitHub Release only" in release_process
    assert "PyPI is not part of the `1.0.0` release" in release_process


def test_source_distribution_manifest_includes_license():
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "include LICENSE" in manifest.splitlines()
