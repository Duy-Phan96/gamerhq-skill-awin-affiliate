from .imports import AwinHtmlCreativeSource, CreativeImportError
from .models import Creative, CreativeState
from .skill import (
    DESCRIBE_API,
    IMPORT_HTML_API,
    LIST_CREATIVES_API,
    SKILL_ID,
    STORAGE_KEY,
    AwinAffiliateSkill,
)


def create_skill():
    return AwinAffiliateSkill()


__all__ = [
    "AwinAffiliateSkill",
    "AwinHtmlCreativeSource",
    "Creative",
    "CreativeImportError",
    "CreativeState",
    "DESCRIBE_API",
    "IMPORT_HTML_API",
    "LIST_CREATIVES_API",
    "SKILL_ID",
    "STORAGE_KEY",
    "create_skill",
]
