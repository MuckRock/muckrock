"""Tests for HTML sanitization"""

# MuckRock
from muckrock.core.sanitize import clean_html


def test_keeps_allowed_tags_and_attributes():
    html = '<b>bold</b> <a href="https://www.muckrock.com/" title="home">link</a>'
    assert clean_html(html) == html


def test_strips_disallowed_tags_but_keeps_their_text():
    assert clean_html("<p>para</p> <foo>bar</foo>") == "para bar"


def test_drops_script_content():
    assert clean_html("safe<script>alert('xss')</script>") == "safe"


def test_strips_event_handlers_and_javascript_urls():
    html = '<a href="javascript:alert(1)" onclick="alert(1)">x</a>'
    assert clean_html(html) == "<a>x</a>"


def test_does_not_add_rel_to_links():
    assert "rel=" not in clean_html('<a href="https://www.muckrock.com/">x</a>')


def test_escapes_text():
    assert clean_html("Tom & Jerry, 1 < 2") == "Tom &amp; Jerry, 1 &lt; 2"


def test_strips_all_tags_when_none_allowed():
    assert clean_html("<b>bold</b> & <i>italic</i>", tags=()) == "bold &amp; italic"


def test_filters_style_properties():
    html = '<p style="color: red; position: absolute">x</p>'
    cleaned = clean_html(
        html,
        tags={"p"},
        attributes={"p": {"style"}},
        filter_style_properties={"color"},
    )
    assert cleaned == '<p style="color:red">x</p>'
