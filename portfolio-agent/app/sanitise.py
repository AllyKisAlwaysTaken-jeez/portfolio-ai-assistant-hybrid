import bleach

ALLOWED_TAGS = [
    "html","head","body","main","section","nav","header","footer","article","aside",
    "h1","h2","h3","h4","p","a","img","ul","ol","li","strong","em","span","div",
    "table","thead","tbody","tr","td","th","figure","figcaption"
]
ALLOWED_ATTRIBUTES = {
    "*": ["class", "id", "role"],
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "width", "height"]
}

def sanitize_html(raw_html: str) -> str:
    cleaned = bleach.clean(raw_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    # optionally also strip javascript: URLs in href/src
    cleaned = bleach.linkify(cleaned)
    return cleaned
