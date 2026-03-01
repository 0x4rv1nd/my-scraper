#this file is used to clean the urls

import json

INPUT = "oneplus_links.ndjson"
OUTPUT = "oneplus_clean_links.ndjson"

clean = set()

with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        url = json.loads(line)["url"]

        # keep only real phone pages
        if "-price-in-india" not in url:
            continue

        if "?" in url:
            continue

        if "/list-of-" in url:
            continue

        if any(x in url for x in ["earbuds","earphones","headphones"]):
            continue

        clean.add(url)

with open(OUTPUT, "w", encoding="utf-8") as f:
    for url in sorted(clean):
        f.write(json.dumps({"url": url}) + "\n")

print("Clean phones:", len(clean))
