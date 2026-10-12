from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    path = ROOT / relative
    assert path.is_file(), f"Missing release-governance file: {relative}"
    return path.read_text(encoding="utf-8")


def test_release_process_requires_exact_main_artifact_evidence():
    process = _read("docs/release-process.md")

    assert "on pull requests, validating the proposed merged tree" in process
    assert "on every push to `main`, validating the exact post-merge commit" in process
    assert "through manual `workflow_dispatch`" in process
    assert "Pull-request evidence proves the proposed tree" in process
    assert "does not replace the successful `main`-push run" in process
    assert "Issue #33 branch protection" in process


def test_project_status_tracks_all_owner_controlled_1_0_gates():
    status = _read("docs/project-status.md")

    assert "Decision — License identity and distribution channel" in status
    assert "Decision — Main branch protection" in status
    assert "Tracker: Issue #23" in status
    assert "Tracker: Issue #33" in status
    assert "exact post-merge `main` artifact dry run" in status
    assert "A successful Skill release does not authorize" in status
