# VerifiedAgents — US Insurance Agents Scraper & Interactive Dashboard

## Overview
- **Part 1 (Data Extraction Pipeline):** High-performance asynchronous Python crawler (`auto_crawler.py`) built with `curl_cffi`, `Playwright`, and `BeautifulSoup` that bypasses Cloudflare security layers, parses verified US insurance agent profiles into SQLite (`verifiedagents_data.db`), and exports submissions to `VerifiedAgents_Submission.xlsx`.
- **Part 2 (Interactive Dashboard):** Fast, standalone static dashboard generator (`build_dashboard.py`) that enriches records with parsed geographic dimensions (`State`, `City`, `ZIP Code`) and compiles `VerifiedAgents_Dashboard.html` featuring 8 dynamic KPI metric cards, two-tier hierarchical dropdown filters, an expandable all-field filter drawer, client-side search, multi-column sorting, pagination, and filtered CSV export.

---

## Manager Updates & Pipeline Enhancements

### 1. Fetching Additional Profiles (1.3M+ National Directory)
- **Initial State:** The first crawl processed sitemaps `1` through `122`, capturing **244,000** agent profiles.
- **Root Cause & Scope:** VerifiedAgent.com hosts a national registry containing over **1,310,000+** insurance agent listings across an estimated **655+ sitemaps** (`verifiedagent-agents-1.xml` to `verifiedagent-agents-655.xml`).
- **Solution:** Added automated sitemap ingestion to `auto_crawler.py`:
  ```bash
  # Ingest and queue all remaining sitemaps (e.g. from 123 to 655)
  ./venv/bin/python auto_crawler.py --seed-sitemaps 123 655

  # Resume asynchronous crawling on the expanded pending queue
  ./venv/bin/python auto_crawler.py --crawl
  ```

### 2. Missing Email Recovery & Cloudflare XOR De-Obfuscation
- **Initial State:** Only **890** emails were extracted out of 244,000 profiles (0.4% coverage).
- **Root Cause Analysis:** VerifiedAgent.com operates behind Cloudflare with **Email Address Obfuscation** enabled. Cloudflare converts public email addresses into encrypted hex payloads:
  `<a class="__cf_email__" href="/cdn-cgi/l/email-protection#..." data-cfemail="[HEX]">[email protected]</a>`
  The original regex and substring checks (`if "@" in val`) failed on the plaintext `[email protected]`, discarding valid emails. Furthermore, schema markup and custom Elementor headings were ignored.
- **Engine Fixes Implemented:**
  1. **Cloudflare XOR De-obfuscator:** Added `decode_cf_email()` to decrypt both `data-cfemail` attributes and `/cdn-cgi/l/email-protection#[HEX]` link fragments.
  2. **Schema.org Structured Data Parser:** Extracts direct `email` properties from embedded `<script type="application/ld+json">` Person / LocalBusiness tags.
  3. **Elementor Widget Heading Extractor:** Checks custom Elementor contact containers if `#agent-email-addresses` is absent.
  4. **Data Sanitization:** Stripped `[email protected]` text artifacts from `location` and extracted misplaced emails mistakenly parsed into `websites`.
- **Email Backfill / Recovery Command:**
  ```bash
  # Re-crawl existing profiles missing emails to backfill them with the upgraded engine
  ./venv/bin/python auto_crawler.py --retry-missing-emails 10000
  ```

---

## Repository Contents
- `auto_crawler.py` — High-concurrency scraping engine with Cloudflare bypass, sitemap discovery, email de-obfuscation, and database management.
- `verifiedagents_data.db` — SQLite database storing indexed tables `agents` and `url_queue`.
- `VerifiedAgents_Submission.xlsx` — Cleaned Excel dataset formatted for submission.
- `build_dashboard.py` — High-speed dashboard builder supporting direct SQLite querying (`--source db`) and Excel fallback.
- `VerifiedAgents_Dashboard.html` — Interactive light-themed analytical web dashboard.
- `agents_chunk_*.js` — Sharded data chunks (50,000 records per chunk) powering the client-side dashboard without UI lag.

---

## CLI Commands Reference

### Pipeline & Scraper (`auto_crawler.py`)
```bash
# Display dataset coverage statistics and queue status
./venv/bin/python auto_crawler.py --stats

# Discover and queue URLs from additional sitemaps
./venv/bin/python auto_crawler.py --seed-sitemaps 123 655

# Run high-concurrency crawler on pending URLs
./venv/bin/python auto_crawler.py --crawl

# Backfill missing emails for existing records (e.g. up to 10,000 profiles)
./venv/bin/python auto_crawler.py --retry-missing-emails 10000

# Export SQLite database to VerifiedAgents_Submission.xlsx
./venv/bin/python auto_crawler.py --export
```

### Dashboard Generator (`build_dashboard.py`)
```bash
# Fast-build dashboard directly from SQLite (recommended, ~10s for 244k records)
./venv/bin/python build_dashboard.py --source db

# Build dashboard from Excel file
./venv/bin/python build_dashboard.py --source excel
```

---

## How to Run Locally
1. Activate the Python virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Inspect current dataset statistics:
   ```bash
   python auto_crawler.py --stats
   ```
3. Rebuild the interactive dashboard:
   ```bash
   python build_dashboard.py --source db
   ```
4. Open `VerifiedAgents_Dashboard.html` in your web browser.
