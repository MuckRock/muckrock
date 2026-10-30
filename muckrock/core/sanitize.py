"""
HTML sanitization
"""

# Third Party
import nh3

# Same as bleach's defaults, which nh3's much broader defaults would otherwise widen
ALLOWED_TAGS = frozenset(
    [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "code",
        "em",
        "i",
        "li",
        "ol",
        "strong",
        "ul",
    ]
)
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "abbr": {"title"},
    "acronym": {"title"},
}


def clean_html(html, tags=ALLOWED_TAGS, attributes=None, **kwargs):
    """Sanitize HTML, stripping any tag or attribute not allowed.

    Disallowed tags are removed but their text kept, except for script and
    style, whose content is dropped too.
    """
    if attributes is None:
        attributes = ALLOWED_ATTRIBUTES
    # The nofollow filter adds its own rel, and browsers ignore a second one
    kwargs.setdefault("link_rel", None)
    return nh3.clean(
        html,
        tags=set(tags),
        attributes={tag: set(attrs) for tag, attrs in attributes.items()},
        **kwargs,
    )
