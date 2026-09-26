"""
PriceDrop QA - Tech News fetcher
Runs on GitHub Actions every 30 minutes, reads RSS feeds and writes news.json.
Only headline, short summary, image, source and link are stored (no full articles).
"""
import json, re, html, time, hashlib
from datetime import datetime, timezone
from urllib.parse import quote_plus
import feedparser

UA = "Mozilla/5.0 (compatible; PriceDropQA-NewsBot/1.0; +https://pricedropqa.github.io)"
MAX_ITEMS = 200          # total items kept in news.json
PER_SOURCE = 40          # max items taken from one feed
SUMMARY_LEN = 220        # characters

def gnews(query):
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"

# Each source: list of feed URLs tried in order; the last one is a Google News fallback.
SOURCES = [
    {"id": "androidpolice", "name": "Android Police", "cat": "android",
     "urls": ["https://www.androidpolice.com/feed/", gnews("site:androidpolice.com")]},
    {"id": "xda", "name": "XDA", "cat": "android",
     "urls": ["https://www.xda-developers.com/feed/", gnews("site:xda-developers.com")]},
    {"id": "9to5mac", "name": "9to5Mac", "cat": "iphone",
     "urls": ["https://9to5mac.com/feed/", gnews("site:9to5mac.com")]},
    {"id": "redmondpie", "name": "Redmond Pie", "cat": "iphone",
     "urls": ["https://www.redmondpie.com/feed/", "https://feeds.feedburner.com/RedmondPie",
              gnews("site:redmondpie.com")]},
    {"id": "tomsguide", "name": "Tom's Guide", "cat": "general",
     "urls": ["https://www.tomsguide.com/feeds.xml", gnews("site:tomsguide.com")]},
    # Topic feeds (many publishers, via Google News)
    {"id": "gn-android", "name": "Android News", "cat": "android", "topic": True,
     "urls": [gnews("android phone OR samsung galaxy OR google pixel when:2d")]},
    {"id": "gn-iphone", "name": "iPhone News", "cat": "iphone", "topic": True,
     "urls": [gnews("iphone OR ios when:2d")]},
]

ANDROID_WORDS = r"\b(android|pixel|galaxy|samsung|oneplus|xiaomi|redmi|poco|oppo|vivo|realme|motorola|nothing phone|honor|huawei|wear ?os)\b"
IPHONE_WORDS = r"\b(iphone|ios|ipad|ipados|apple|airpods|macos|watchos|mac|macbook)\b"
# Skip clearly off-topic items (e.g. fitness/movies on Tom's Guide)
OFFTOPIC_WORDS = r"\b(workout|recipe|movie|movies|netflix|hbo|disney\+|mattress|grand final|nfl|nba|premier league|horoscope|wordle|connections hints?)\b"

TAG_RE = re.compile(r"<[^>]+>")
IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)

def clean(text):
    text = html.unescape(TAG_RE.sub(" ", text or ""))
    return re.sub(r"\s+", " ", text).strip()

def short(text, n=SUMMARY_LEN):
    text = clean(text)
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0].rstrip(",.;:") + "…"

def find_image(e):
    for key in ("media_content", "media_thumbnail"):
        for m in e.get(key, []) or []:
            if m.get("url"):
                return m["url"]
    for l in e.get("links", []):
        if l.get("rel") == "enclosure" and str(l.get("type", "")).startswith("image"):
            return l.get("href")
    for field in ("summary", "content"):
        val = e.get(field)
        if isinstance(val, list):
            val = " ".join(v.get("value", "") for v in val)
        m = IMG_RE.search(val or "")
        if m:
            return m.group(1)
    return None

def published(e):
    for k in ("published_parsed", "updated_parsed"):
        t = e.get(k)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return datetime.now(timezone.utc)

def categorize(title, summary, default):
    text = f"{title} {summary}".lower()
    a = bool(re.search(ANDROID_WORDS, text))
    i = bool(re.search(IPHONE_WORDS, text))
    if a and not i:
        return "android"
    if i and not a:
        return "iphone"
    return default

def fetch_source(src):
    for url in src["urls"]:
        try:
            d = feedparser.parse(url, agent=UA)
            if d.entries:
                return d.entries[:PER_SOURCE], url
            print(f"  empty: {url} (status {d.get('status')})")
        except Exception as ex:
            print(f"  failed: {url}: {ex}")
    return [], None

def main():
    items, seen_links, seen_titles = [], set(), set()
    report = {}
    for src in SOURCES:
        print(f"Fetching {src['name']}…")
        entries, used = fetch_source(src)
        count = 0
        for e in entries:
            title = clean(e.get("title"))
            link = e.get("link")
            if not title or not link:
                continue
            source_name = src["name"]
            # Google News titles end with " - Publisher"
            if "news.google.com" in (used or ""):
                pub = (e.get("source") or {}).get("title")
                if pub:
                    source_name = pub if src.get("topic") else src["name"]
                    title = re.sub(r"\s+-\s+" + re.escape(pub) + r"$", "", title)
            summary = short(e.get("summary", ""))
            if summary.lower().startswith(title.lower()[:40]):
                summary = ""  # Google News summaries just repeat the title
            if re.search(OFFTOPIC_WORDS, title.lower()):
                continue
            key = re.sub(r"[^a-z0-9]", "", title.lower())[:60]
            if link in seen_links or key in seen_titles:
                continue
            seen_links.add(link); seen_titles.add(key)
            items.append({
                "id": hashlib.md5(link.encode()).hexdigest()[:12],
                "title": title,
                "summary": summary,
                "link": link,
                "image": find_image(e),
                "source": source_name,
                "sourceId": src["id"],
                "category": categorize(title, summary, src["cat"]),
                "published": published(e).isoformat(),
            })
            count += 1
        report[src["id"]] = {"items": count, "feed": used}
        print(f"  {count} items from {used}")

    items.sort(key=lambda x: x["published"], reverse=True)
    out = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "sources": report,
        "items": items[:MAX_ITEMS],
    }
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"Saved {len(out['items'])} items to news.json")

if __name__ == "__main__":
    main()
