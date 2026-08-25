import re
import time
from collections import deque
from html.parser import HTMLParser
from threading import Lock
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

CACHE = {}
CACHE_LOCK = Lock()
CACHE_SECONDS = 60
MAX_PAGES = 12
MAX_CHARS_PER_PAGE = 18000
MAX_TOTAL_CHARS = 70000
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/151.0 Safari/537.36 "
    "MUKA-AI-Website-Knowledge/1.0"
)

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.links = []
        self.in_script = False
        self.in_style = False
        self.in_noscript = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style"}:
            self.in_script = True
        if tag == "noscript":
            self.in_noscript = True
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style"}:
            self.in_script = False
        if tag == "noscript":
            self.in_noscript = False

    def handle_data(self, data):
        if self.in_script or self.in_style or self.in_noscript:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.text_parts.append(text)

    def get_text(self):
        return " ".join(self.text_parts)


def normalize_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    path = parsed.path or "/"
    normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"
    if normalized.endswith("/") and path != "/":
        normalized = normalized.rstrip("/")
    return normalized


def same_domain(url, base_url):
    try:
        a = urlparse(url).netloc.lower().replace("www.", "")
        b = urlparse(base_url).netloc.lower().replace("www.", "")
        return a == b
    except Exception:
        return False


def fetch_html(url):
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=12) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type.lower():
            return ""
        data = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return data.decode(charset, errors="replace")


def parse_page(url, html):
    parser = PageParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    text = parser.get_text()[:MAX_CHARS_PER_PAGE]
    links = []
    for link in parser.links:
        normalized = normalize_url(urljoin(url, link))
        if normalized and same_domain(normalized, url):
            links.append(normalized)
    return {"url": url, "text": text, "links": links}


def get_live_website_knowledge(website):
    if not website:
        return {"success": False, "website": "", "pages": [], "text": "", "error": "Website not configured."}
    website = normalize_url(website)
    now = time.time()
    with CACHE_LOCK:
        cached = CACHE.get(website)
    if cached and now - cached["timestamp"] < CACHE_SECONDS:
        return cached["data"]

    visited = set()
    queue = deque([website])
    pages = []
    total_chars = 0

    while queue and len(pages) < MAX_PAGES:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        try:
            html = fetch_html(current)
            if not html:
                continue
            page = parse_page(current, html)
            if not page["text"]:
                continue
            remaining = MAX_TOTAL_CHARS - total_chars
            if remaining <= 0:
                break
            page["text"] = page["text"][:remaining]
            pages.append({"url": page["url"], "text": page["text"]})
            total_chars += len(page["text"])
            for link in page["links"]:
                if link not in visited and link not in queue:
                    queue.append(link)
        except Exception as error:
            print(f"WEBSITE FETCH ERROR [{current}]: {type(error).__name__}: {error}")

    parts = []
    for page in pages:
        parts.append(
            f"\n===== SOURCE PAGE =====\nURL: {page['url']}\n{page['text']}\n===== END SOURCE PAGE =====\n"
        )

    result = {
        "success": bool(pages),
        "website": website,
        "pages": pages,
        "text": "\n".join(parts),
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": None if pages else "No readable website pages found.",
    }

    with CACHE_LOCK:
        CACHE[website] = {"timestamp": now, "data": result}
    return result
