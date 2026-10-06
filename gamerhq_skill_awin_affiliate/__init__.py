from .client import AwinApiClient, AwinApiError, PublisherAccount
from .connection import AwinConnection, ConnectionStatus
from .imports import AwinHtmlCreativeSource, CreativeImportError
from .models import Creative, CreativeState
from .skill import (
    ACCESS_TOKEN_SECRET_KEY,
    CONNECTION_STORAGE_KEY,
    DESCRIBE_API,
    IMPORT_HTML_API,
    LIST_CREATIVES_API,
    SETUP_CONNECT_API,
    SETUP_DISCONNECT_API,
    SETUP_SELECT_PUBLISHER_API,
    SETUP_STATUS_API,
    SKILL_ID,
    STORAGE_KEY,
    AwinAffiliateSkill,
)


def create_skill():
    return AwinAffiliateSkill()


__all__ = [
    "ACCESS_TOKEN_SECRET_KEY",
    "AwinAffiliateSkill",
    "AwinApiClient",
    "AwinApiError",
    "AwinConnection",
    "AwinHtmlCreativeSource",
    "CONNECTION_STORAGE_KEY",
    "ConnectionStatus",
    "Creative",
    "CreativeImportError",
    "CreativeState",
    "DESCRIBE_API",
    "IMPORT_HTML_API",
    "LIST_CREATIVES_API",
    "PublisherAccount",
    "SETUP_CONNECT_API",
    "SETUP_DISCONNECT_API",
    "SETUP_SELECT_PUBLISHER_API",
    "SETUP_STATUS_API",
    "SKILL_ID",
    "STORAGE_KEY",
    "create_skill",
]
