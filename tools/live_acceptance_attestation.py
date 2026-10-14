from __future__ import annotations

import re
from datetime import date
from pathlib import Path

REPORT_PATH = "docs/live-acceptance-report.md"
REQUIRED_KEYS = (
    "LIVE_ACCEPTANCE_STATUS",
    "LIVE_ACCEPTANCE_APPROVED_BY",
    "LIVE_ACCEPTANCE_APPROVED_AT",
    "LIVE_ACCEPTANCE_REVIEWED_COMMIT",
)
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def parse_attestation(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in REQUIRED_KEYS:
            values[key] = value.strip()
    return values


def collect_live_acceptance_errors(root: Path) -> tuple[str, ...]:
    path = root / REPORT_PATH
    if not path.is_file():
        return (
            f"Stable 1.x release candidates require an approved {REPORT_PATH} file.",
        )

    text = path.read_text(encoding="utf-8")
    values = parse_attestation(text)
    errors: list[str] = []

    missing = [key for key in REQUIRED_KEYS if not values.get(key)]
    if missing:
        errors.append(
            "Live acceptance attestation is missing required fields: "
            + ", ".join(missing)
            + "."
        )
        return tuple(errors)

    if values["LIVE_ACCEPTANCE_STATUS"] != "PASS":
        errors.append("Live acceptance status must be PASS for a stable 1.x release.")

    approved_by = values["LIVE_ACCEPTANCE_APPROVED_BY"]
    if (
        "<" in approved_by
        or ">" in approved_by
        or approved_by.lower() in {"name", "owner", "reviewer", "tbd"}
    ):
        errors.append("Live acceptance approver must be a real, non-placeholder identity.")

    approved_at = values["LIVE_ACCEPTANCE_APPROVED_AT"]
    try:
        date.fromisoformat(approved_at)
    except ValueError:
        errors.append("Live acceptance approval date must use ISO format YYYY-MM-DD.")

    reviewed_commit = values["LIVE_ACCEPTANCE_REVIEWED_COMMIT"]
    if not COMMIT_SHA.fullmatch(reviewed_commit):
        errors.append(
            "Live acceptance reviewed commit must be a lowercase 40-character SHA."
        )

    return tuple(errors)
