import asyncio
import re
import sqlite3
import logging
from bs4 import BeautifulSoup
import pandas as pd
from curl_cffi.requests import AsyncSession
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DB_PATH = "verifiedagents_data.db"
USER_DATA_DIR = "./edge_browser_profile"
SCRAPED_BY = "Dhruv Shetty"
CONCURRENCY = 42
BATCH_SIZE = 3000

def extract_section_widget(soup, heading_text):
    h3 = soup.find(lambda t: t.name == "h3" and heading_text.lower() in t.get_text().lower())
    if not h3:
        return None
    widget_heading = h3.find_parent(class_=re.compile(r"elementor-widget-heading"))
    if not widget_heading:
        return None
    return widget_heading.find_next_sibling(class_=re.compile(r"elementor-widget"))

def parse_profile(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    full_name = ""
    h1 = soup.find("h1")
    if h1:
        for br in h1.find_all("br"):
            br.replace_with(" ")
        raw_name = h1.get_text(separator=" ", strip=True)
        full_name = re.sub(r"Insurance\s*Agent.*$", "", raw_name, flags=re.IGNORECASE).strip()
        full_name = re.sub(r"\s*[✓✔]?\s*Claimed.*$", "", full_name, flags=re.IGNORECASE).strip()

    npn_match = re.search(r"NPN\s*[:#-]?\s*(\d+)", soup.get_text(), re.IGNORECASE)
    if npn_match:
        npn = npn_match.group(1)
    else:
        url_match = re.search(r"/(\d{5,10})/", url)
        npn = url_match.group(1) if url_match else ""

    location = ""
    loc_w = extract_section_widget(soup, "Location")
    if loc_w:
        lines = [s.strip() for s in loc_w.stripped_strings if "Service Area" not in s and "helps clients" not in s]
        lines = [l for l in lines if not any(b in l.lower() for b in ["lookup insurance", "site links", "read insurance"])]
        location = ", ".join(lines)

    phone_numbers = []
    phone_sec = soup.find("section", id="agent-phone-numbers")
    if phone_sec and "not provided" not in phone_sec.get_text().lower():
        for a in phone_sec.select("a.va-contact-link, a[href^='tel:']"):
            val = a.get_text(strip=True)
            if val:
                phone_numbers.append(val)
        if not phone_numbers:
            phone_numbers = re.findall(r"\(?\b[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", phone_sec.get_text())
    phone_numbers = list(dict.fromkeys(phone_numbers))

    email_addresses = []
    email_sec = soup.find("section", id="agent-email-addresses")
    if email_sec and "not provided" not in email_sec.get_text().lower():
        for a in email_sec.select("a.va-contact-link, a[href^='mailto:']"):
            val = a.get_text(strip=True) or a["href"].replace("mailto:", "").strip()
            if "@" in val:
                email_addresses.append(val)
        if not email_addresses:
            email_addresses = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", email_sec.get_text())
    email_addresses = list(dict.fromkeys(email_addresses))

    websites = []
    web_sec = soup.find("section", id="agent-websites")
    if web_sec and "not provided" not in web_sec.get_text().lower():
        for a in web_sec.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("http") and "verifiedagent.com" not in href:
                websites.append(href)
    websites = list(dict.fromkeys(websites))

    appointed_companies = []
    carrier_sec = soup.find("section", id="agent-carrier-appointments")
    if carrier_sec and "not provided" not in carrier_sec.get_text().lower():
        pills = carrier_sec.select(".va-pills span, li, .badge, .chip")
        if pills:
            appointed_companies = [p.get_text(strip=True) for p in pills if p.get_text(strip=True)]
        else:
            appointed_companies = [s.strip() for s in carrier_sec.stripped_strings if len(s.strip()) < 80]
    appointed_companies = list(dict.fromkeys(appointed_companies))

    return {
        "profile_page_url": url,
        "full_name": full_name,
        "npn_number": npn,
        "location": location,
        "phone_numbers": " | ".join(phone_numbers),
        "email_addresses": " | ".join(email_addresses),
        "websites": " | ".join(websites),
        "appointed_companies": " | ".join(appointed_companies),
        "scraped_by": SCRAPED_BY
    }

def export_submission():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("""
            SELECT profile_page_url, full_name, npn_number, location,
                   phone_numbers, email_addresses, websites, appointed_companies,
                   scraped_by
            FROM agents ORDER BY npn_number ASC
        """, conn)

    df.insert(0, "s_no", range(1, len(df) + 1))
    target_columns = [
        "s_no", "profile_page_url", "full_name", "npn_number",
        "location", "phone_numbers", "email_addresses", "websites",
        "appointed_companies", "scraped_by"
    ]
    df = df[target_columns]

    with pd.ExcelWriter("VerifiedAgents_Submission.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Submission File (verifiedagents)"[:31], index=False)
    logging.info(f"Excel checkpoint saved: {len(df):,} total verified records.")

async def get_cf_credentials():
    logging.info("Harvesting fresh Cloudflare cookie & User-Agent from browser...")
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        page = await ctx.new_page()
        await page.goto("https://verifiedagent.com/615798/debra-hetzer/", wait_until="domcontentloaded", timeout=30000)
        for _ in range(12):
            if "just a moment" in (await page.title()).lower():
                await page.wait_for_timeout(1000)
            else:
                break
        await page.wait_for_selector("h1", timeout=15000)

        ua = await page.evaluate("navigator.userAgent")
        cookies = await ctx.cookies("https://verifiedagent.com")
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        await ctx.close()
        logging.info(f"Captured {len(cookie_dict)} cookies. Closing browser.")
        return ua, cookie_dict

async def http_worker(worker_id, queue, session, results_buffer, buffer_lock, cf_expired_event):
    while not cf_expired_event.is_set():
        try:
            url = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        try:
            resp = await session.get(url, timeout=15)
            if resp.status_code in (403, 429, 503) or "just a moment" in resp.text[:1000].lower():
                if not cf_expired_event.is_set():
                    logging.warning(f"Worker {worker_id} hit HTTP {resp.status_code} (Cloudflare block).")
                cf_expired_event.set()
                break

            if resp.status_code == 200:
                data = parse_profile(resp.text, url)
                if data["full_name"] and data["full_name"].lower() != "verifiedagent.com":
                    async with buffer_lock:
                        results_buffer.append((data, "completed", url))
                        if len(results_buffer) % 50 == 0:
                            logging.info(f"Progress: {len(results_buffer)}/{BATCH_SIZE} fetched in current batch...")
                else:
                    async with buffer_lock:
                        results_buffer.append((None, "failed", url))
            else:
                logging.warning(f"Unexpected status {resp.status_code} on {url}")
                async with buffer_lock:
                    results_buffer.append((None, "failed", url))
        except Exception as e:
            logging.error(f"Request error on {url}: {e}")
            async with buffer_lock:
                results_buffer.append((None, "failed", url))

def flush_buffer(results_buffer):
    if not results_buffer:
        return 0
    saved = 0
    with sqlite3.connect(DB_PATH) as conn:
        for data, status, url in results_buffer:
            if data:
                conn.execute("""
                    INSERT OR REPLACE INTO agents (
                        profile_page_url, full_name, npn_number, location,
                        phone_numbers, email_addresses, websites,
                        appointed_companies, scraped_by
                    ) VALUES (
                        :profile_page_url, :full_name, :npn_number, :location,
                        :phone_numbers, :email_addresses, :websites,
                        :appointed_companies, :scraped_by
                    )
                """, data)
                saved += 1
            conn.execute("UPDATE url_queue SET status = ? WHERE url = ?", (status, url))
    results_buffer.clear()
    return saved

async def main():
    ua, cookies = await get_cf_credentials()

    while True:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT url FROM url_queue WHERE status = 'pending' LIMIT ?", (BATCH_SIZE,)).fetchall()

        if not rows:
            logging.info("All pending URLs processed!")
            break

        queue = asyncio.Queue()
        for r in rows:
            queue.put_nowait(r[0])

        results_buffer = []
        buffer_lock = asyncio.Lock()
        cf_expired_event = asyncio.Event()

        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with AsyncSession(impersonate="chrome", headers=headers, cookies=cookies) as session:
            workers = [
                asyncio.create_task(http_worker(i, queue, session, results_buffer, buffer_lock, cf_expired_event))
                for i in range(CONCURRENCY)
            ]
            await asyncio.gather(*workers)

        saved_count = flush_buffer(results_buffer)
        logging.info(f"Batch complete: +{saved_count} profiles saved.")
        export_submission()

        if cf_expired_event.is_set():
            logging.warning("Cloudflare rejected the HTTP session. Waiting 3s and refreshing cookie...")
            await asyncio.sleep(3)
            ua, cookies = await get_cf_credentials()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped safely by user.")