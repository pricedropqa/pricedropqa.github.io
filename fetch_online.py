"""
PriceDrop QA - online store price fetcher.

Runs on GitHub Actions twice a day (see .github/workflows/update-prices.yml).
Reads the public product feed (products.json) of Shopify stores and writes online.csv,
which the app shows next to the local-shop prices from the Google Sheet.

To add a store or a collection: add a line to STORES below.
  handle = the part after /collections/ in the store's URL
  type   = which app tab it goes to (Phone, Tablet, Watch, Earbuds, Headphones, Speaker, Accessory, Camera)
           or "Audio" = sort each product into Speaker / Headphones / Earbuds / Accessory by its name

To track single product pages from other (non-Shopify) stores, add them to WATCHLIST below.
"""
import csv, json, re, sys, time, datetime, urllib.request

STORES = [
    {"shop": "iConnect Qatar", "base": "https://iconnectqatar.com",
     "collections": [("mobile-phones-price-in-qatar", "Phone"), ("jbl-bluetooth-speaker", "Speaker"),
                     ("jbl-partybox", "Speaker"), ("bose", "Audio")]},
    {"shop": "Digital Zone", "base": "https://digitalzone.qa",
     "collections": [("mobile-phones", "Phone")]},
    {"shop": "Sony World", "base": "https://sonyworld.qa",
     "collections": [("sony-camera-lens-offer", "Camera")]},
    {"shop": "Chordz", "base": "https://chordz.shop",
     "collections": [("sonos", "Audio")]},
    {"shop": "TechBay Qatar", "base": "https://techbayqatar.com",
     "collections": [("marshall", "Audio")]},
]

# Single product pages (any store whose pages carry standard schema.org Product data).
# shop, type, url  +  optional: brand, model, storage (to match other stores), note, link (your affiliate link)
NOON = "https://www.noon.com/qatar-en/"
WATCHLIST = [
    # noon Qatar - flagship phones (one colour per model/storage). Add "link": "https://s.noon.com/..." for affiliate links.
    {"shop": "noon Qatar", "type": "Phone", "brand": "Apple", "model": "iPhone 18 Pro Max", "storage": "256GB", "note": "International version · eSIM only",
     "url": NOON + "iphone-18-pro-max-256gb-esim-only-burgundy-5g-with-facetime-international-version/N70432341V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Apple", "model": "iPhone 18 Pro Max", "storage": "512GB", "note": "International version · eSIM only",
     "url": NOON + "iphone-18-pro-max-512-gb-esim-only-burgundy-5g-with-facetime-international-version/N70432417V/p/",
     "link": "https://s.noon.com/xmttALmutUI"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Apple", "model": "iPhone 18 Pro Max", "storage": "1TB", "note": "Middle East version · eSIM only",
     "url": NOON + "iphone-18-pro-max-1tb-esim-only-burgundy-5g-with-facetime-middle-east-version/N70432408V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Apple", "model": "iPhone 18 Pro", "storage": "256GB", "note": "International version · eSIM only",
     "url": NOON + "iphone-18-pro-256gb-esim-only-black-5g-with-facetime-international-version/N70432367V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Apple", "model": "iPhone 18 Pro", "storage": "512GB", "note": "International version · eSIM only",
     "url": NOON + "iphone-18-pro-512-gb-esim-only-silver-5g-with-facetime-international-version/N70432336V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Samsung", "model": "Galaxy Z Fold 8", "storage": "256GB", "note": "Middle East version",
     "url": NOON + "galaxy-z-fold-8-dual-sim-graphite-12gb-ram-256gb-5g-middle-east-version/N70395347V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Samsung", "model": "Galaxy Z Fold 8", "storage": "512GB", "note": "Middle East version",
     "url": NOON + "galaxy-z-fold-8-dual-sim-graphite-12gb-ram-512gb-5g-middle-east-version/N70395350V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Samsung", "model": "Galaxy Z Fold 8", "storage": "1TB", "note": "Middle East version",
     "url": NOON + "galaxy-z-fold-8-dual-sim-graphite-16gb-ram-1tb-5g-middle-east-version/N70395344V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Samsung", "model": "Galaxy Z Fold 8 Ultra", "storage": "512GB", "note": "Middle East version",
     "url": NOON + "galaxy-z-fold-8-ultra-dual-sim-violet-shadow-12gb-ram-512gb-5g-middle-east-version/N70395359V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Samsung", "model": "Galaxy S26 Ultra", "storage": "256GB", "note": "Middle East version",
     "url": NOON + "galaxy-s26-ultra-dual-sim-black-12gb-ram-256gb-5g-middle-east-version/N70283855V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Samsung", "model": "Galaxy S26 Ultra", "storage": "512GB", "note": "Middle East version",
     "url": NOON + "galaxy-s26-ultra-dual-sim-black-12gb-ram-512gb-5g-middle-east-version/N70283859V/p/"},
    {"shop": "noon Qatar", "type": "Phone", "brand": "Samsung", "model": "Galaxy S25 Ultra", "storage": "256GB", "note": "Middle East version",
     "url": NOON + "galaxy-s25-ultra-ai-dual-sim-titanium-black-12gb-ram-256gb-5g-middle-east-version/N70140491V/p/"},
]

DELAY = 4  # seconds between requests to the same store (be polite)

# Price tiers (QR) per device type: [Flagship from, Mid-Range from, Budget from]; below = Low End
TIERS = {
    "Phone":   [2500, 1200, 500],
    "Tablet":  [3000, 1500, 700],
    "Watch":   [1500, 700, 250],
    "Earbuds": [800, 400, 150],
    "Headphones": [1200, 600, 200],
    "Speaker": [2000, 800, 300],
    "Camera":  [8000, 4000, 1500],
    "Accessory": [400, 150, 60],
}

# Show the store's own product photos? Only turn on if the store agreed.
USE_STORE_IMAGES = False

BRANDS = ["Apple", "Samsung", "Xiaomi", "Redmi", "Poco", "Honor", "Huawei", "Oppo", "Vivo", "Realme",
          "OnePlus", "Google", "Nothing", "Tecno", "Infinix", "Nokia", "Motorola", "TCL", "Sony", "Lenovo",
          "ZTE", "Nubia", "Itel", "Anker", "JBL", "Canon", "Nikon", "Fujifilm", "DJI", "GoPro", "Asus", "Meizu",
          "Sonos", "Bose", "Marshall", "Bang & Olufsen", "Harman Kardon", "Ultimate Ears", "Beats", "Soundcore",
          "Sennheiser", "Beyerdynamic", "Jabra", "Skullcandy", "Devialet", "Bowers & Wilkins", "Denon", "Yamaha"]
BRAND_FIX = {b.lower(): b for b in BRANDS}

COLUMNS = ["type", "tier", "brand", "model", "storage", "shop", "area", "price", "old_price", "offer",
           "in_stock", "whatsapp", "phone", "map_url", "updated", "image", "ram", "display", "camera",
           "battery", "chipset", "youtube", "url"]

UA = "Mozilla/5.0 (compatible; PriceDropQA/1.0; +https://pricedropqa.github.io/; contact: pricedropqa@gmail.com)"


def get_json(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"  retry {i + 1} after error: {e}")
            time.sleep(5 * (i + 1))


SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(GB|TB)\b", re.I)


def sizes(text):
    out = []
    for n, u in SIZE_RE.findall(text or ""):
        gb = float(n) * (1024 if u.upper() == "TB" else 1)
        out.append((gb, f"{n}{u.upper()}"))
    return out


def storage_of(text):
    """Largest GB/TB value = storage (the smaller one is RAM)."""
    s = sizes(text)
    return max(s)[1] if s else ""


def ram_of(text):
    s = sorted(sizes(text))
    if len(s) >= 2 and s[0][0] <= 24:
        return s[0][1]
    m = re.search(r"(\d+)\s*GB\s*RAM", text or "", re.I)
    return m.group(1) + "GB" if m else ""


def clean_model(title, brand):
    t = re.split(r"\s+[-–—|]\s+", title)[0]           # drop " - Colour" / " – 12GB, 256GB"
    t = re.sub(r"\s+-\s*[A-Za-z][A-Za-z ]*$", "", t)   # drop " -Silver"
    t = re.sub(r"\(.*?\)", " ", t)
    t = SIZE_RE.sub(" ", t)
    t = re.sub(r"\b(RAM|ROM|Storage|5G|4G|LTE|Dual\s*SIM|Smart\s*phone|Smartphone|Mobile\s*Phone|Unlocked|in Qatar)\b", " ", t, flags=re.I)
    t = t.replace("&amp;", "&")
    t = re.sub(r"[,+/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if brand and t.lower().startswith(brand.lower() + " "):
        t = t[len(brand) + 1:]
    return t.strip(" -")


def brand_of(product):
    vendor = (product.get("vendor") or "").strip()
    if vendor.lower() in BRAND_FIX:
        return BRAND_FIX[vendor.lower()]
    title = (product.get("title") or "").replace("&amp;", "&").lower()
    for b in sorted(BRANDS, key=len, reverse=True):   # "Bang & Olufsen" before "Bang"
        if title.startswith(b.lower() + " "):
            return b
    first = title.split(" ")[0] if title else ""
    return BRAND_FIX.get(first, first.title())


def audio_kind(title, ptype=""):
    """Sort an audio product into the right tab by its name."""
    t = f"{title} {ptype}".lower()
    if re.search(r"\b(case|cover|strap|cable|adapter|mount|stand|bracket|charger|charging|dock|wall|cushion|ear ?pads?|bag|pouch|sleeve|backpack|skin|remote|battery pack)\b", t):
        return "Accessory"
    if re.search(r"\b(buds|earbuds?|earphones?|in-ear|tws|airpods|earfun)\b", t):
        return "Earbuds"
    if re.search(r"\b(headphones?|headset|over-ear|on-ear|major|monitor ii|quietcomfort ultra headphones)\b", t):
        return "Headphones"
    return "Speaker"


def tier_of(kind, price):
    a, b, c = TIERS.get(kind, TIERS["Phone"])
    return "Flagship" if price >= a else "Mid-Range" if price >= b else "Budget" if price >= c else "Low End"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def rows_for_product(p, kind, store, today):
    if kind == "Audio":
        kind = audio_kind(p.get("title", ""), p.get("product_type", ""))
    brand = brand_of(p)
    title = p.get("title", "")
    model = clean_model(title, brand)
    if not model:
        return []
    groups = {}
    for v in p.get("variants", []):
        vt = " ".join(str(v.get(k) or "") for k in ("title", "option1", "option2", "option3"))
        storage = storage_of(vt) or storage_of(title)
        if not storage and kind == "Camera":  # cameras: keep "Body" and "Body+Kit Lens" apart
            opt = str(v.get("option1") or v.get("title") or "").split("/")[0]
            opt = re.split(r"\s+[-\u2013]\s+", opt)[0].strip()  # "Body - Black" -> "Body"
            if re.search(r"body|kit|lens", opt, re.I):
                storage = opt
        price = num(v.get("price"))
        if price <= 0:
            continue
        cand = {"price": price, "old": num(v.get("compare_at_price")), "avail": bool(v.get("available")),
                "ram": ram_of(vt) or ram_of(title)}
        best = groups.get(storage)
        # prefer in-stock, then cheapest
        if best is None or (cand["avail"], -cand["price"]) > (best["avail"], -best["price"]):
            groups[storage] = cand
    img = ""
    if USE_STORE_IMAGES and p.get("images"):
        img = p["images"][0].get("src", "")
    out = []
    for storage, g in groups.items():
        out.append({
            "type": kind, "tier": tier_of(kind, g["price"]), "brand": brand, "model": model,
            "storage": storage, "shop": store["shop"], "area": "Online store",
            "price": f"{g['price']:.0f}", "old_price": f"{g['old']:.0f}" if g["old"] > g["price"] else "",
            "offer": "", "in_stock": "Yes" if g["avail"] else "No", "whatsapp": "", "phone": "", "map_url": "",
            "updated": today, "image": img, "ram": g["ram"], "display": "", "camera": "", "battery": "",
            "chipset": "", "youtube": "", "url": f"{store['base']}/products/{p.get('handle', '')}",
        })
    return out


def fetch_store(store, today):
    rows = []
    for handle, kind in store["collections"]:
        page = 1
        while page <= 60:
            url = f"{store['base']}/collections/{handle}/products.json?limit=50&page={page}"
            try:
                data = get_json(url)
            except Exception as e:
                if rows:  # keep what we already have from earlier pages
                    print(f"  {store['shop']}: stopped at page {page} ({e})")
                    break
                raise
            products = data.get("products", [])
            if not products:
                break
            for p in products:
                rows += rows_for_product(p, kind, store, today)
            page += 1
            time.sleep(DELAY)  # be polite
    return rows


def fetch_watchlist(today):
    """Read price + stock from the schema.org Product data on single product pages."""
    rows = []
    for w in WATCHLIST:
        url, kind, shop = w["url"], w["type"], w["shop"]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=60) as r:
                html = r.read().decode("utf-8", "replace")
            product = None
            for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S | re.I):
                try:
                    data = json.loads(block)
                except ValueError:
                    continue
                items = data.get("@graph", [data]) if isinstance(data, dict) else data
                for it in items if isinstance(items, list) else [items]:
                    if isinstance(it, dict) and "Product" in str(it.get("@type")) and it.get("offers"):
                        product = it
                        break
                if product:
                    break
            if not product:
                print(f"  watchlist: no product data on {url}")
                continue
            offer = product["offers"][0] if isinstance(product["offers"], list) else product["offers"]
            price = num(offer.get("price") or offer.get("lowPrice"))
            if price <= 0:
                continue
            title = re.sub(r"\s+[-–]\s+[A-Za-z ]+$", "", product.get("name", "")).replace("&amp;", "&")
            b = product.get("brand")
            fake = {"title": title, "vendor": b.get("name", "") if isinstance(b, dict) else (b or "")}
            brand = w.get("brand") or brand_of(fake)
            note = [w["note"]] if w.get("note") else []
            seller = (offer.get("seller") or {}).get("name") if isinstance(offer.get("seller"), dict) else ""
            if seller and seller.lower() not in shop.lower():
                note.append(f"Sold by {seller}")
            try:
                sd = offer["shippingDetails"]["deliveryTime"]
                lo = sd["handlingTime"]["minValue"] + sd["transitTime"]["minValue"]
                hi = sd["handlingTime"]["maxValue"] + sd["transitTime"]["maxValue"]
                note.append(f"Delivery {lo}-{hi} days")
            except (KeyError, TypeError):
                pass
            rows.append({
                "type": kind, "tier": tier_of(kind, price), "brand": brand,
                "model": w.get("model") or clean_model(title, brand), "storage": w.get("storage", ""),
                "shop": shop, "area": "Online store", "price": f"{price:.0f}", "old_price": "",
                "offer": " · ".join(note), "in_stock": "Yes" if "InStock" in str(offer.get("availability")) else "No",
                "whatsapp": "", "phone": "", "map_url": "", "updated": today, "image": "", "ram": "", "display": "",
                "camera": "", "battery": "", "chipset": "", "youtube": "", "url": w.get("link") or url,
            })
        except Exception as e:
            print(f"  watchlist: failed {url} ({e})")
        time.sleep(DELAY)
    return rows


def main():
    today = datetime.date.today().isoformat()
    all_rows, report = [], []
    for store in STORES:
        try:
            rows = fetch_store(store, today)
            all_rows += rows
            report.append(f"{store['shop']}: {len(rows)} rows")
        except Exception as e:  # one broken store must not stop the others
            report.append(f"{store['shop']}: FAILED ({e})")
    wl = fetch_watchlist(today)
    all_rows += wl
    report.append(f"Watchlist: {len(wl)} rows")
    print("\n".join(report))
    if not all_rows:
        print("Nothing fetched - keeping the old online.csv")
        sys.exit(1)
    # one row per shop + phone + storage: keep in-stock first, then the cheapest
    best = {}
    for r in all_rows:
        key = (r["shop"], r["type"], r["brand"].lower(), r["model"].lower(), r["storage"].lower())
        cur = best.get(key)
        score = (r["in_stock"] == "Yes", -float(r["price"]))
        if cur is None or score > (cur["in_stock"] == "Yes", -float(cur["price"])):
            best[key] = r
    all_rows = list(best.values())
    print(f"{len(all_rows)} rows after removing duplicate colours")
    with open("online.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(all_rows, key=lambda r: (r["type"], r["brand"], r["model"], r["storage"], r["shop"])))


if __name__ == "__main__":
    main()
