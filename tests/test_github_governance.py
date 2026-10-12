from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    path = ROOT / relative
    assert path.is_file(), f"Missing repository governance file: {relative}"
    return path.read_text(encoding="utf-8")


def test_issue_forms_require_safe_actionable_evidence():
    bug = _read(".github/ISSUE_TEMPLATE/bug_report.yml")
    feature = _read(".github/ISSUE_TEMPLATE/feature_request.yml")
    config = _read(".github/ISSUE_TEMPLATE/config.yml")

    assert "Reproduction steps" in bug
    assert "Expected behavior" in bug
    assert "Actual behavior" in bug
    assert "P0 — security, data integrity, or release-blocking failure" in bug
    assert "removed all tokens, secrets" in bug

    assert "User problem" in feature
    assert "Expected user or business value" in feature
    assert "Scope classification" in feature
    assert "Public contract, storage, capability, or migration impact" in feature
    assert "does not require this project to modify another repository" in feature

    assert "blank_issues_enabled: false" in config
    assert "SECURITY.md" in config
    assert "CONTRIBUTING.md" in config


def test_pull_request_template_covers_release_and_repository_boundaries():
    template = _read(".github/PULL_REQUEST_TEMPLATE.md")

    for heading in (
        "## Summary",
        "## Tests and evidence",
        "## Public contract impact",
        "## Storage and migration impact",
        "## Security and capability impact",
        "## Release status",
    ):
        assert heading in template

    assert "HANDOFF REQUIRED" in template
    assert "python -m tools.release_preflight" in template
    assert "Python 3.12 / 3.13 / 3.14" in template
    assert "No downstream GamerHQ deployment" in template


def test_codeowners_covers_repository_security_and_release_files():
    codeowners = _read(".github/CODEOWNERS")

    assert "* @Duy-Phan96" in codeowners
    assert "SECURITY.md @Duy-Phan96" in codeowners
    assert ".github/workflows/ @Duy-Phan96" in codeowners
    assert "tools/ @Duy-Phan96" in codeowners
