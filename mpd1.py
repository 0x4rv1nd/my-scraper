#multi page Downloader with spec score in json format
import asyncio
import json
import os
import random
import re
from playwright.async_api import async_playwright

INPUT = "samsung_clean_links.ndjson"
SAVE_DIR = "pages_browser"
PROGRESS = "downloaded.json"
CONCURRENCY = 5

os.makedirs(SAVE_DIR, exist_ok=True)

# ---------- LOAD URLS ----------
urls = []
with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        urls.append(json.loads(line)["url"])

# ---------- PROGRESS ----------
downloaded = set()
if os.path.exists(PROGRESS):
    downloaded = set(json.load(open(PROGRESS)))

def save_progress():
    with open(PROGRESS, "w") as f:
        json.dump(list(downloaded), f)

def filename_from_url(url):
    name = url.rstrip("/").split("/")[-1]
    html_file = os.path.join(SAVE_DIR, name + ".html")
    json_file = os.path.join(SAVE_DIR, name + ".json")
    return html_file, json_file


# ---------- WORKER ----------
async def download_worker(context, queue, worker_id):

    while True:

        url = await queue.get()
        html_file, json_file = filename_from_url(url)

        if url in downloaded or os.path.exists(html_file):
            queue.task_done()
            continue

        page = await context.new_page()

        try:
            print(f"[Worker {worker_id}] Opening:", url)

            await page.goto(url, timeout=90000)

            # wait for full render
            await page.wait_for_selector("h1", timeout=60000)
            await page.wait_for_timeout(random.randint(5000, 8000))

            # -------- EXTRACT SPEC SCORE (LIVE DOM) --------
            spec_score = None
            try:
                score_el = page.locator('[data-score-title="Spec Score"]').first
                text = await score_el.inner_text()
                spec_score = re.search(r"\d+", text).group()
                print(f"[Worker {worker_id}] Score: {spec_score}")
            except:
                print(f"[Worker {worker_id}] Score not found")

            # -------- SAVE HTML --------
            html = await page.content()
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html)

            # -------- SAVE SCORE FILE --------
            meta = {
                "spec_score": spec_score
            }
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            downloaded.add(url)
            save_progress()

            print(f"[Worker {worker_id}] Saved ✓")

        except Exception as e:
            print(f"[Worker {worker_id}] FAILED:", url, e)

        finally:
            await page.close()
            await asyncio.sleep(random.randint(3,6))
            queue.task_done()


# ---------- MAIN ----------
async def main():

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False,
            slow_mo=80,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )

        queue = asyncio.Queue()

        for url in urls:
            if url not in downloaded:
                queue.put_nowait(url)

        workers = [
            asyncio.create_task(download_worker(context, queue, i+1))
            for i in range(CONCURRENCY)
        ]

        await queue.join()

        for w in workers:
            w.cancel()

        await browser.close()

asyncio.run(main())