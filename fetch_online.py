"""
PriceDrop QA - online store price fetcher.

Runs on GitHub Actions twice a day (see .github/workflows/update-prices.yml).
Reads the public product feed (products.json) of Shopify stores and writes online.csv,
which the app shows next to the local-shop prices from the Google Sheet.

To add a store or a collection: add a line to STORES below.
  handle = the part after /collections/ in the store's URL
  type   = which app tab it goes to (Phone, Tablet, Watch, Earbuds, Accessory, Camera)
"""
import csv, json, re, sys, time, datetime, urllib.request

STORES = [
    {"shop": "iConnect Qatar", "base": "https://iconnectqatar.com",
     "collections": [("mobile-phones-price-in-qatar", "Phone")]},
    {"shop": "Digital Zone", "base": "https://digitalzone.qa",
     "collections": [("mobile-phones", "Phone")]},
    {"shop": "Sony World", "base": "https://sonyworld.qa",
     "collections": [("sony-camera-lens-offer", "Camera")]},
]

# Price tiers (QR) per device type: [Flagship from, Mid-Range from, Budget from]; below = Low End
TIERS = {
    "Phone":   [2500, 1200, 500],
    "Tablet":  [3000, 1500, 700],
    "Watch":   [1500, 700, 250],
    "Earbuds": [800, 400, 150],
    "Camera":  [8000, 4000, 1500],
    "Accessory": [400, 150, 60],
}

# Show the store's own product photos? Only turn on if the store agreed.
USE_STORE_IMAGES = False

BRANDS = ["Apple", "Samsung", "Xiaomi", "Redmi", "Poco", "Honor", "Huawei", "Oppo", "Vivo", "Realme",
          "OnePlus", "Google", "Nothing", "Tecno", "Infinix", "Nokia", "Motorola", "TCL", "Sony", "Lenovo",
          "ZTE", "Nubia", "Itel", "Anker", "JBL", "Canon", "Nikon", "Fujifilm", "DJI", "GoPro", "Asus", "Meizu"]
BRAND_FIX = {b.lower(): b for b in BRANDS}

COLUMNS = ["type", "tier", "brand", "model", "storage", "shop", "area", "price", "old_price", "offer",
           "in_stock", "whatsapp", "phone", "map_url", "updated", "image", "ram", "display", "camera",
           "battery", "chipset", "youtube", "url"]

UA = "Mozilla/5.0 (compatible; PriceDropQA/1.0; +https://pricedropqa.github.io/)"


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


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
    t = re.sub(r"\(.*?\)", " ", t)
    t = SIZE_RE.sub(" ", t)
    t = re.sub(r"\b(RAM|ROM|Storage|5G|4G|LTE|Dual\s*SIM|Smart\s*phone|Smartphone|Mobile\s*Phone|Unlocked)\b", " ", t, flags=re.I)
    t = re.sub(r"[,+/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if brand and t.lower().startswith(brand.lower() + " "):
        t = t[len(brand) + 1:]
    return t.strip(" -")


def brand_of(product):
    vendor = (product.get("vendor") or "").strip()
    if vendor.lower() in BRAND_FIX:
        return BRAND_FIX[vendor.lower()]
    first = (product.get("title") or "").split(" ")[0]
    return BRAND_FIX.get(first.lower(), first)


def tier_of(kind, price):
    a, b, c = TIERS.get(kind, TIERS["Phone"])
    return "Flagship" if price >= a else "Mid-Range" if price >= b else "Budget" if price >= c else "Low End"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def rows_for_product(p, kind, store, today):
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
            opt = str(v.get("option1") or v.get("title") or "").split("/")[0].strip()
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
        while page <= 20:
            url = f"{store['base']}/collections/{handle}/products.json?limit=250&page={page}"
            data = get_json(url)
            products = data.get("products", [])
            if not products:
                break
            for p in products:
                rows += rows_for_product(p, kind, store, today)
            page += 1
            time.sleep(2)  # be polite
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
    print("\n".join(report))
    if not all_rows:
        print("Nothing fetched - keeping the old online.csv")
        sys.exit(1)
    with open("online.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(all_rows, key=lambda r: (r["type"], r["brand"], r["model"], r["storage"], r["shop"])))


if __name__ == "__main__":
    main()
