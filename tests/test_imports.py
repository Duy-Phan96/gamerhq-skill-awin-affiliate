import pytest

from gamerhq_skill_awin_affiliate import AwinHtmlCreativeSource, CreativeImportError


HTML = """
<!-- START ADVERTISER: Ugovaper from awin.com -->
<a rel="sponsored" href="https://www.awin1.com/cread.php?s=4902463&v=129591&q=615955&r=3095707">
  <img src="https://www.awin1.com/cshow.php?s=4902463&v=129591&q=615955&r=3095707">
</a>
<!-- END ADVERTISER: Ugovaper from awin.com -->
"""


def test_parses_awin_banner_into_normalized_creative():
    creative = AwinHtmlCreativeSource().parse(HTML)[0]

    assert creative.provider == "awin"
    assert creative.advertiser_name == "Ugovaper"
    assert creative.publisher_id == "3095707"
    assert creative.advertiser_id == "129591"
    assert creative.external_creative_id == "4902463"
    assert creative.creative_group_id == "615955"
    assert creative.type == "image"
    assert creative.id == "awin:3095707:129591:4902463"


def test_deduplicates_same_creative_in_one_import():
    result = AwinHtmlCreativeSource().parse(HTML + HTML)
    assert len(result) == 1


def test_rejects_non_awin_tracking_url():
    bad = HTML.replace("https://www.awin1.com/cread.php", "https://example.com/redirect")
    with pytest.raises(CreativeImportError, match="not an Awin URL"):
        AwinHtmlCreativeSource().parse(bad)


def test_rejects_missing_required_tracking_parameter():
    bad = HTML.replace("&r=3095707", "")
    with pytest.raises(CreativeImportError, match="parameter 'r'"):
        AwinHtmlCreativeSource().parse(bad)
