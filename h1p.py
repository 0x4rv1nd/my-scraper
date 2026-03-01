import os
import json
import re
from bs4 import BeautifulSoup

PAGES_DIR = "pages_browser"
OUTPUT = "xiaomi_clean_dataset.json"

phones = []

def clean(t):
    return " ".join(t.split())


def extract_json_ld(soup):
    """Extract structured product data"""
    data = {}

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            j = json.loads(script.string)

            if isinstance(j, dict) and j.get("@type") == "Product":
                data["name"] = j.get("name")
                data["brand"] = j.get("brand", {}).get("name")

                if "image" in j:
                    data["images"] = j["image"]

                if "offers" in j:
                    data["price"] = j["offers"].get("price")
                    data["currency"] = j["offers"].get("priceCurrency")
                    data["availability"] = j["offers"].get("availability")

                if "aggregateRating" in j:
                    data["rating_value"] = j["aggregateRating"].get("ratingValue")
                    data["rating_count"] = j["aggregateRating"].get("ratingCount")

        except:
            pass

    return data


def extract_product_id(html):
    m = re.search(r'var productId\s*=\s*"(\d+)"', html)
    return m.group(1) if m else None


def extract_specs(soup):
    specs = {}

    sections = soup.select("section[id]")

    for sec in sections:
        category = sec.get("id")

        table = sec.select_one("table.key-specs-info")
        if not table:
            continue

        for row in table.select("tr"):
            cols = row.select("td")
            if len(cols) != 2:
                continue

            key = clean(cols[0].get_text())
            val = clean(cols[1].get_text())

            specs[f"{category} | {key}"] = val

    return specs


def extract_key_specs(soup):
    ks = []
    for li in soup.select(".key-specs li, .key_specs li"):
        txt = clean(li.get_text())
        if txt:
            ks.append(txt)
    return ks


# ---------------- PARSE ----------------

files = [f for f in os.listdir(PAGES_DIR) if f.endswith(".html")]

for i, file in enumerate(files, 1):

    path = os.path.join(PAGES_DIR, file)
    print(f"[{i}/{len(files)}] {file}")

    with open(path, encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")

    phone = {}

    # structured data
    phone.update(extract_json_ld(soup))

    # product id
    phone["product_id"] = extract_product_id(html)

    # specs
    phone["specifications"] = extract_specs(soup)

    # key specs
    phone["key_specs_summary"] = extract_key_specs(soup)

    phones.append(phone)

# save
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(phones, f, indent=2, ensure_ascii=False)

print("\nDONE — Clean dataset created:", OUTPUT)