#this file is    used to get the urls of the samsung products 1
import json
import asyncio
from playwright.async_api import async_playwright

OUTPUT = "vivo_links.ndjson"

seen = set()

def save(url):
    if url in seen:
        return
    seen.add(url)
    with open(OUTPUT, "a", encoding="utf-8") as f:
        f.write(json.dumps({"url": url}) + "\n")
        f.flush()


async def run():

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible browser
        context = await browser.new_context()
        page = await context.new_page()

        print("Opening vivo page...")
        await page.goto("https://www.91mobiles.com/list-of-phones/vivo-mobile-price-list-in-india")

        # wait Cloudflare + initial load
        await page.wait_for_timeout(8000)

        while True:

            print("Scrolling...")

            # scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(5000)

            # extract product links
            links = await page.eval_on_selector_all(
                "a",
                "els => els.map(e => e.href).filter(h => h.includes('-price-in-india'))"
            )

            new = 0
            for link in links:
                if "91mobiles.com" in link:
                    if link not in seen:
                        save(link)
                        print("✔", link)
                        new += 1

            print("New links:", new)

            # stop condition
            load_more = await page.query_selector("text=Load More")
            if not load_more:
                print("All vivo phones collected ✓")
                break

            await load_more.click()
            await page.wait_for_timeout(6000)

        await browser.close()

asyncio.run(run())
