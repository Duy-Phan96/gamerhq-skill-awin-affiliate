from __future__ import annotations

from html.parser import HTMLParser
import re
from urllib.parse import parse_qs, urlparse

from .models import Creative, CreativeState


class CreativeImportError(ValueError):
    pass


_ADVERTISER_COMMENT = re.compile(
    r"START\s+ADVERTISER:\s*(?P<name>.+?)\s+from\s+awin\.com",
    re.IGNORECASE,
)


class _AwinSnippetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.advertiser_name: str | None = None
        self._anchor_href: str | None = None
        self._anchor_rel: set[str] = set()
        self._image_src: str | None = None
        self.rows: list[tuple[str, str, str | None]] = []

    def handle_comment(self, data: str) -> None:
        match = _ADVERTISER_COMMENT.search(data.strip())
        if match:
            self.advertiser_name = match.group("name").strip()

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {str(key).lower(): value for key, value in attrs}
        if tag.lower() == "a":
            self._anchor_href = values.get("href")
            rel = values.get("rel") or ""
            self._anchor_rel = {part.lower() for part in str(rel).split()}
            self._image_src = None
        elif tag.lower() == "img" and self._anchor_href:
            self._image_src = values.get("src")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a":
            return
        if self._anchor_href and self._image_src:
            self.rows.append((self._anchor_href, self._image_src, self.advertiser_name))
        self._anchor_href = None
        self._anchor_rel = set()
        self._image_src = None


def _validated_awin_url(value: str, *, label: str) -> str:
    raw = str(value).strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"https", "http"}:
        raise CreativeImportError(f"{label} must use http or https.")
    if host not in {"awin1.com", "www.awin1.com", "awin.com", "www.awin.com"} and not host.endswith(".awin1.com"):
        raise CreativeImportError(f"{label} is not an Awin URL.")
    return raw


def _single(query: dict[str, list[str]], key: str, *, required: bool = True) -> str | None:
    values = query.get(key) or []
    value = values[0].strip() if values else ""
    if required and not value:
        raise CreativeImportError(f"Awin creative URL is missing required parameter '{key}'.")
    return value or None


class AwinHtmlCreativeSource:
    source_id = "manual_html"

    def parse(self, html: str, *, advertiser_name: str | None = None) -> list[Creative]:
        if not isinstance(html, str) or not html.strip():
            raise CreativeImportError("Awin HTML is required.")

        parser = _AwinSnippetParser()
        parser.feed(html)
        parser.close()
        if not parser.rows:
            raise CreativeImportError("No supported Awin image creative was found in the supplied HTML.")

        creatives: list[Creative] = []
        seen: set[str] = set()
        for tracking_raw, image_raw, comment_name in parser.rows:
            tracking_url = _validated_awin_url(tracking_raw, label="Tracking URL")
            image_url = _validated_awin_url(image_raw, label="Image URL")
            tracking_query = parse_qs(urlparse(tracking_url).query, keep_blank_values=False)

            creative_id = _single(tracking_query, "s")
            advertiser_id = _single(tracking_query, "v")
            publisher_id = _single(tracking_query, "r")
            creative_group_id = _single(tracking_query, "q", required=False)

            stable_id = f"awin:{publisher_id}:{advertiser_id}:{creative_id}"
            if stable_id in seen:
                continue
            seen.add(stable_id)

            creatives.append(
                Creative(
                    id=stable_id,
                    provider="awin",
                    publisher_id=publisher_id or "",
                    advertiser_id=advertiser_id or "",
                    external_creative_id=creative_id or "",
                    creative_group_id=creative_group_id,
                    advertiser_name=(advertiser_name or comment_name or "").strip() or None,
                    type="image",
                    image_url=image_url,
                    tracking_url=tracking_url,
                    source=self.source_id,
                    state=CreativeState.ACTIVE,
                    metadata={"queryKeys": sorted(tracking_query.keys())},
                )
            )

        return creatives
