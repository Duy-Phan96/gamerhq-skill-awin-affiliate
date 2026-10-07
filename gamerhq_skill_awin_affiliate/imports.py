from __future__ import annotations

from html.parser import HTMLParser
import re
from urllib.parse import parse_qs, urlparse

from .creative_sources import CreativeSnapshot, CreativeSourceAuthority
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
        self._image_alt: str | None = None
        self._image_title: str | None = None
        self._image_width: int | None = None
        self._image_height: int | None = None
        self.rows: list[tuple[str, str, str | None, str | None, str | None, int | None, int | None]] = []

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
            self._image_alt = None
            self._image_title = None
            self._image_width = None
            self._image_height = None
        elif tag.lower() == "img" and self._anchor_href:
            self._image_src = values.get("src")
            self._image_alt = (values.get("alt") or "").strip() or None
            self._image_title = (values.get("title") or "").strip() or None
            try:
                self._image_width = int(values["width"]) if values.get("width") else None
                self._image_height = int(values["height"]) if values.get("height") else None
            except (TypeError, ValueError):
                self._image_width = None
                self._image_height = None

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a":
            return
        if self._anchor_href and self._image_src:
            self.rows.append((
                self._anchor_href,
                self._image_src,
                self.advertiser_name,
                self._image_alt,
                self._image_title,
                self._image_width,
                self._image_height,
            ))
        self._anchor_href = None
        self._anchor_rel = set()
        self._image_src = None
        self._image_alt = None
        self._image_title = None
        self._image_width = None
        self._image_height = None


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
    authority = CreativeSourceAuthority.UPSERT_ONLY

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
        for tracking_raw, image_raw, comment_name, image_alt, image_title, width, height in parser.rows:
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
                    title=image_title or image_alt,
                    description=image_alt if image_title and image_alt != image_title else None,
                    image_url=image_url,
                    tracking_url=tracking_url,
                    width=width,
                    height=height,
                    source=self.source_id,
                    state=CreativeState.ACTIVE,
                    metadata={"queryKeys": sorted(tracking_query.keys())},
                )
            )

        return creatives

    def snapshot(self, html: str, *, advertiser_name: str | None = None) -> CreativeSnapshot:
        creatives = self.parse(html, advertiser_name=advertiser_name)
        publisher_ids = {creative.publisher_id for creative in creatives}
        advertiser_ids = {creative.advertiser_id for creative in creatives}
        if len(publisher_ids) != 1 or len(advertiser_ids) != 1:
            raise CreativeImportError(
                "One manual HTML import must contain creatives from exactly one publisher and advertiser."
            )
        return CreativeSnapshot(
            source_id=self.source_id,
            authority=self.authority,
            publisher_id=next(iter(publisher_ids)),
            advertiser_id=next(iter(advertiser_ids)),
            creatives=tuple(creatives),
        )


class AwinSavedPageCreativeSource(AwinHtmlCreativeSource):
    """Parse a saved/exported My Creative HTML page without automating Awin login.

    A saved page may include multiple advertisers, so it returns one snapshot per
    publisher + advertiser scope. Every scope is UPSERT_ONLY unless the caller
    explicitly marks exactly one advertiser as a complete snapshot.
    """

    source_id = "saved_my_creative_html"

    def snapshots(
        self,
        html: str,
        *,
        complete_advertiser_id: str | None = None,
    ) -> tuple[CreativeSnapshot, ...]:
        creatives = self.parse(html)
        groups: dict[tuple[str, str], list[Creative]] = {}
        for creative in creatives:
            groups.setdefault(
                (creative.publisher_id, creative.advertiser_id),
                [],
            ).append(creative)

        complete = str(complete_advertiser_id or "").strip() or None
        if complete is not None and complete not in {advertiser for _, advertiser in groups}:
            raise CreativeImportError(
                "completeAdvertiserId was not found in the supplied Awin HTML."
            )

        snapshots: list[CreativeSnapshot] = []
        for (publisher_id, advertiser_id), items in sorted(groups.items()):
            normalized_items = tuple(
                Creative.from_dict({**item.to_dict(), "source": self.source_id})
                for item in items
            )
            snapshots.append(
                CreativeSnapshot(
                    source_id=self.source_id,
                    authority=(
                        CreativeSourceAuthority.AUTHORITATIVE
                        if advertiser_id == complete
                        else CreativeSourceAuthority.UPSERT_ONLY
                    ),
                    publisher_id=publisher_id,
                    advertiser_id=advertiser_id,
                    creatives=normalized_items,
                )
            )
        return tuple(snapshots)
