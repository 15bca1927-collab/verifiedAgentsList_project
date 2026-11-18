# VerifiedAgents — US Insurance Agents Scraper & Interactive Dashboard

## Overview
- **Part 1 (Data Extraction):** Asynchronous Python scraping pipeline (`auto_crawler.py`) built with `Playwright`, `curl_cffi`, and `BeautifulSoup` that harvests 244,000 US insurance agent records into SQLite and exports the final dataset to `VerifiedAgents_Submission.xlsx`.
- **Part 2 (Interactive Dashboard):** `build_dashboard.py` parses geographic helper fields (`State`, `City`, `ZIP Code`) from `VerifiedAgents_Submission.xlsx` and generates `VerifiedAgents_Dashboard.html` featuring 8 dynamic KPI cards, dropdown-first categorization filters, an expandable all-header filter drawer, pagination, sorting, and filtered CSV export.

## Repository Contents
- `auto_crawler.py` — Part 1 asynchronous crawler and data extraction pipeline.
- `VerifiedAgents_Submission.xlsx` — Final cleaned dataset containing 244,000 verified US insurance agent records.
- `build_dashboard.py` — Part 2 dashboard generator that parses geographic fields and builds the static HTML/JS dashboard assets.
- `VerifiedAgents_Dashboard.html` — Interactive light-themed dashboard UI.

## How to Build & Run the Dashboard Locally
1. Clone this repository and open the project directory:
   ```bash
   git clone [https://github.com/15bca1927-collab/verifiedAgentsList_project.git](https://github.com/15bca1927-collab/verifiedAgentsList_project.git)
   cd verifiedAgentsList_project

2. Set up a Python virtual environment, install dependencies, and generate the local data chunks:
  python3 -m venv venv
  source venv/bin/activate
  pip install pandas openpyxl
  python3 build_dashboard.py

3. Open VerifiedAgents_Dashboard.html in your web browser.