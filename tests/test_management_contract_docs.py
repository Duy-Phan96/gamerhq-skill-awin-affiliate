import re
from pathlib import Path

from gamerhq_skill_awin_affiliate import AwinAffiliateSkill


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = ROOT / "docs" / "management-api-contracts.md"


def documented_contract_ids() -> tuple[str, ...]:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    return tuple(re.findall(r"^## `([^`]+)`$", text, flags=re.MULTILINE))


def manifest_contract_ids() -> tuple[str, ...]:
    return tuple(
        contract.id
        for contract in AwinAffiliateSkill.manifest.management_apis.exposes
    )


def test_management_contract_document_covers_manifest_exactly_once():
    documented = documented_contract_ids()
    declared = manifest_contract_ids()

    assert len(documented) == len(set(documented))
    assert set(documented) == set(declared)
    assert len(documented) == len(declared)


def test_critical_contract_rules_are_explicitly_documented():
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "forward `confirmPayload` unchanged" in text
    assert "`groups` is always the numeric count" in text
    assert "Detailed rows are always in `groupResults`" in text
    assert "no raw Awin token" in text
    assert "one aggregate campaign-store lock per guild" in text
