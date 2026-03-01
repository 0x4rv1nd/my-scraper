import asyncio
import json
import re
import random
import os
from playwright.async_api import async_playwright

INPUT = "oneplus_clean_links.ndjson"
OUTPUT = "oneplus_spec_scores.json"
PROGRESS = "oneplus_spec_progress.json"
CONCURRENCY = 6   # 5–6 is safe

# ---------------- LOAD URLS ----------------
urls = []
with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        urls.append(json.loads(line)["url"])

# already done
done = set()
if os.path.exists(PROGRESS):
    done = set(json.load(open(PROGRESS)))


def save_progress():
    with open(PROGRESS, "w") as f:
        json.dump(list(done), f)


results = []
if os.path.exists(OUTPUT):
    try:
        results = json.load(open(OUTPUT))
    except:
        results = []


def save_result(data):
    results.append(data)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


# ---------------- EXTRACTION ----------------
async def extract_score(context, url, worker_id):

    if url in done:
        return

    page = await context.new_page()

    try:
        print(f"[Worker {worker_id}] Opening:", url)

        await page.goto(url, timeout=90000)

        # wait for product page
        await page.wait_for_selector("h1", timeout=60000)
        await page.wait_for_timeout(2500)

        # get spec score
        try:
            el = page.locator('[data-score-title="Spec Score"]').first
            text = await el.inner_text()
            score = re.search(r'\d+', text).group()
        except:
            score = None

        save_result({
            "url": url,
            "spec_score": score
        })

        done.add(url)
        save_progress()

        print(f"[Worker {worker_id}] Score:", score)

    except Exception as e:
        print(f"[Worker {worker_id}] FAILED:", url)

    finally:
        await page.close()
        await asyncio.sleep(random.randint(2,5))


# ---------------- WORKER ----------------
async def worker(queue, context, worker_id):
    while True:
        url = await queue.get()
        await extract_score(context, url, worker_id)
        queue.task_done()


# ---------------- MAIN ----------------
async def main():

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False,
            slow_mo=120,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )

        queue = asyncio.Queue()

        for url in urls:
            if url not in done:
                queue.put_nowait(url)

        # create workers (tabs)
        workers = [
            asyncio.create_task(worker(queue, context, i+1))
            for i in range(CONCURRENCY)
        ]

        await queue.join()

        for w in workers:
            w.cancel()

        await browser.close()

asyncio.run(main())