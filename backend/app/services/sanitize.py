"""富文本 HTML 白名单过滤（NFR-18 XSS 防护）。

存储原始 HTML 前必须过滤；前台出参也建议再过滤一次。
使用 bleach 允许列表，禁止 script/iframe/on* 事件属性等。
"""
from __future__ import annotations

import bleach

_ALLOWED_TAGS = [
    "p", "br", "strong", "b", "em", "i", "u", "s", "blockquote", "code",
    "pre", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "a",
    "img", "span", "div", "figure", "figcaption", "hr", "table", "thead",
    "tbody", "tr", "td", "th", "video", "source",
]

_ALLOWED_ATTRS = {
    "*": ["class", "style", "id", "align"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "width", "height", "loading"],
    "video": ["src", "poster", "controls", "width", "height"],
    "source": ["src", "type"],
}

_ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]


def sanitize_html(html: str | None) -> str | None:
    if not html:
        return html
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
