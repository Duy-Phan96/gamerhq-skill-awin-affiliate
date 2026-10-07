from .awin_api import AwinAccount, AwinApiError, AwinClient, AwinProgramme
from .creative_sources import CreativeSnapshot, CreativeSource, CreativeSourceAuthority
from .imports import AwinHtmlCreativeSource, CreativeImportError
from .models import Creative, CreativeState
from .sync import CreativeSyncResult, apply_creative_snapshot
from .skill import (
    ADVERTISERS_LIST_API,
    DESCRIBE_API,
    GET_CREATIVE_API,
    PREVIEW_CREATIVE_API,
    POST_PREVIEW_API,
    POST_SEND_API,
    SET_ADVERTISER_CREATIVES_ENABLED_API,
    SET_CREATIVES_ENABLED_API,
    IMPORT_HTML_API,
    SETUP_ACCOUNTS_API,
    SETUP_CONNECT_API,
    SETUP_DISCONNECT_API,
    SETUP_SELECT_PUBLISHER_API,
    SETUP_STATUS_API,
    LIST_CREATIVES_API,
    SKILL_ID,
    STORAGE_KEY,
    AwinAffiliateSkill,
)


def create_skill():
    return AwinAffiliateSkill()


__all__ = [
    "ADVERTISERS_LIST_API",
    "AwinAccount",
    "AwinAffiliateSkill",
    "AwinApiError",
    "AwinClient",
    "AwinProgramme",
    "AwinHtmlCreativeSource",
    "Creative",
    "CreativeSnapshot",
    "CreativeSource",
    "CreativeSourceAuthority",
    "CreativeSyncResult",
    "CreativeImportError",
    "CreativeState",
    "apply_creative_snapshot",
    "DESCRIBE_API",
    "GET_CREATIVE_API",
    "PREVIEW_CREATIVE_API",
    "POST_PREVIEW_API",
    "POST_SEND_API",
    "SET_ADVERTISER_CREATIVES_ENABLED_API",
    "SET_CREATIVES_ENABLED_API",
    "IMPORT_HTML_API",
    "SETUP_ACCOUNTS_API",
    "SETUP_CONNECT_API",
    "SETUP_DISCONNECT_API",
    "SETUP_SELECT_PUBLISHER_API",
    "SETUP_STATUS_API",
    "LIST_CREATIVES_API",
    "SKILL_ID",
    "STORAGE_KEY",
    "create_skill",
]
