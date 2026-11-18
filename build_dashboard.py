import json
import math
import re
from collections import Counter
import pandas as pd

EXCEL_FILE = "VerifiedAgents_Submission.xlsx"
OUTPUT_HTML = "VerifiedAgents_Dashboard.html"
CHUNK_SIZE = 50000

US_STATE_MAP = {
    "AL": "AL", "ALABAMA": "AL", "AK": "AK", "ALASKA": "AK", "AZ": "AZ", "ARIZONA": "AZ",
    "AR": "AR", "ARKANSAS": "AR", "CA": "CA", "CALIFORNIA": "CA", "CO": "CO", "COLORADO": "CO",
    "CT": "CT", "CONNECTICUT": "CT", "DE": "DE", "DELAWARE": "DE", "FL": "FL", "FLORIDA": "FL",
    "GA": "GA", "GEORGIA": "GA", "HI": "HI", "HAWAII": "HI", "ID": "ID", "IDAHO": "ID",
    "IL": "IL", "ILLINOIS": "IL", "IN": "IN", "INDIANA": "IN", "IA": "IA", "IOWA": "IA",
    "KS": "KS", "KANSAS": "KS", "KY": "KY", "KENTUCKY": "KY", "LA": "LA", "LOUISIANA": "LA",
    "ME": "ME", "MAINE": "ME", "MD": "MD", "MARYLAND": "MD", "MA": "MA", "MASSACHUSETTS": "MA",
    "MI": "MI", "MICHIGAN": "MI", "MN": "MN", "MINNESOTA": "MN", "MS": "MS", "MISSISSIPPI": "MS",
    "MO": "MO", "MISSOURI": "MO", "MT": "MT", "MONTANA": "MT", "NE": "NE", "NEBRASKA": "NE",
    "NV": "NV", "NEVADA": "NV", "NH": "NH", "NEW HAMPSHIRE": "NH", "NJ": "NJ", "NEW JERSEY": "NJ",
    "NM": "NM", "NEW MEXICO": "NM", "NY": "NY", "NEW YORK": "NY", "NC": "NC", "NORTH CAROLINA": "NC",
    "ND": "ND", "NORTH DAKOTA": "ND", "OH": "OH", "OHIO": "OH", "OK": "OK", "OKLAHOMA": "OK",
    "OR": "OR", "OREGON": "OR", "PA": "PA", "PENNSYLVANIA": "PA", "RI": "RI", "RHODE ISLAND": "RI",
    "SC": "SC", "SOUTH CAROLINA": "SC", "SD": "SD", "SOUTH DAKOTA": "SD", "TN": "TN", "TENNESSEE": "TN",
    "TX": "TX", "TEXAS": "TX", "UT": "UT", "UTAH": "UT", "VT": "VT", "VERMONT": "VT",
    "VA": "VA", "VIRGINIA": "VA", "WA": "WA", "WASHINGTON": "WA", "WV": "WV", "WEST VIRGINIA": "WV",
    "WI": "WI", "WISCONSIN": "WI", "WY": "WY", "WYOMING": "WY", "DC": "DC", "PR": "PR"
}

def parse_geo(loc: str):
    if not loc:
        return "", "", ""
    zip_match = re.search(r'\b(\d{5})(?:-\d{4})?\b', loc)
    zip_code = zip_match.group(1) if zip_match else ""
    cleaned = re.sub(r',?\s*United States\s*$', '', loc, flags=re.IGNORECASE).strip()
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    state, city = "", ""
    for i in range(len(parts) - 1, -1, -1):
        part_upper = re.sub(r'\b\d{5}(?:-\d{4})?\b', '', parts[i]).strip().upper().strip(".")
        if part_upper in US_STATE_MAP:
            state = US_STATE_MAP[part_upper]
            if i > 0:
                city = parts[i - 1].title()
            break
    return state, city, zip_code

print(f"Reading {EXCEL_FILE}...")
xls = pd.ExcelFile(EXCEL_FILE)
df = pd.read_excel(EXCEL_FILE, sheet_name=xls.sheet_names[0], dtype=str).fillna("")

geo_parsed = df["location"].apply(parse_geo)
df["state"] = [g[0] for g in geo_parsed]
df["city"] = [g[1] for g in geo_parsed]
df["zip_code"] = [g[2] for g in geo_parsed]

cols = [
    "s_no", "profile_page_url", "full_name", "npn_number", "location",
    "phone_numbers", "email_addresses", "websites", "appointed_companies",
    "scraped_by", "state", "city", "zip_code"
]
for c in cols:
    if c not in df.columns:
        df[c] = ""

records = df[cols].values.tolist()
num_chunks = math.ceil(len(records) / CHUNK_SIZE)

script_tags = []
for idx in range(num_chunks):
    chunk = records[idx * CHUNK_SIZE : (idx + 1) * CHUNK_SIZE]
    fname = f"agents_chunk_{idx}.js"
    with open(fname, "w", encoding="utf-8") as cf:
        cf.write("window.RAW_DATA.push(...(")
        json.dump(chunk, cf, separators=(",", ":"))
        cf.write("));\n")
    script_tags.append(f'<script src="{fname}"></script>')

states_list = sorted([s for s in df["state"].unique() if s])
scraped_by_list = sorted([s for s in df["scraped_by"].unique() if s])

comp_counter = Counter()
for val in df["appointed_companies"]:
    if val:
        for item in val.split("|"):
            clean_item = item.strip()
            if clean_item:
                comp_counter[clean_item] += 1
top_companies = [c for c, _ in comp_counter.most_common(300)]

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>VerifiedAgents — US Insurance Agents Dashboard</title>
<style>
  :root {
    --bg: #f1f5f9;
    --card: #ffffff;
    --card-subtle: #f8fafc;
    --row-hover: #eff6ff;
    --border: #cbd5e1;
    --border-light: #e2e8f0;
    --text: #0f172a;
    --muted: #475569;
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --green: #059669;
    --purple: #7c3aed;
    --amber: #d97706;
    --shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: 15px;
    line-height: 1.5;
  }
  header {
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 20px 32px;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    box-shadow: var(--shadow);
  }
  header h1 { margin: 0 0 4px 0; font-size: 1.5rem; font-weight: 700; }
  header span.sub { font-size: 0.92rem; color: var(--muted); }
  .actions { display: flex; gap: 12px; flex-wrap: wrap; }
  button {
    background: var(--primary);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 11px 18px;
    font-size: 0.92rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }
  button:hover { background: var(--primary-hover); }
  button.secondary {
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
  }
  button.secondary:hover { background: var(--card-subtle); }

  .container { max-width: 1680px; margin: 0 auto; padding: 28px 32px; }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }
  .kpi-card {
    background: var(--card);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: var(--shadow);
  }
  .kpi-label {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .kpi-value { font-size: 1.75rem; font-weight: 800; color: var(--primary); line-height: 1.2; }
  .kpi-sub { font-size: 0.84rem; color: var(--muted); margin-top: 6px; }

  .filter-panel {
    background: var(--card);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 28px;
    box-shadow: var(--shadow);
  }
  .filter-top {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding-bottom: 16px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-light);
  }
  .filter-top h2 { margin: 0; font-size: 1.15rem; font-weight: 700; }
  .status-pill {
    background: #eff6ff;
    color: var(--primary);
    border: 1px solid #bfdbfe;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.86rem;
    font-weight: 600;
  }
  .filter-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 18px;
  }
  .filter-group { display: flex; flex-direction: column; gap: 6px; }
  .filter-group label { font-size: 0.88rem; color: var(--text); font-weight: 600; }
  .filter-group input,
  .filter-group select {
    height: 44px;
    background: var(--card-subtle);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    padding: 0 14px;
    font-size: 0.94rem;
    width: 100%;
    transition: border-color 0.15s, background 0.15s;
  }
  .filter-group input:focus,
  .filter-group select:focus {
    outline: none;
    background: #ffffff;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
  }

  details.advanced-drawer {
    margin-top: 22px;
    padding-top: 18px;
    border-top: 1px solid var(--border-light);
  }
  details.advanced-drawer summary {
    cursor: pointer;
    font-weight: 700;
    font-size: 0.92rem;
    color: var(--primary);
    user-select: none;
    list-style: none;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  details.advanced-drawer summary::-webkit-details-marker { display: none; }
  details.advanced-drawer[open] summary { margin-bottom: 16px; }

  .table-card {
    background: var(--card);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow);
  }
  .table-toolbar {
    padding: 16px 24px;
    background: var(--card-subtle);
    border-bottom: 1px solid var(--border-light);
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 14px;
    font-size: 0.94rem;
    font-weight: 500;
  }
  .table-wrap { overflow-x: auto; max-height: 680px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  thead th {
    position: sticky;
    top: 0;
    background: #f8fafc;
    color: var(--text);
    font-weight: 700;
    text-align: left;
    padding: 14px 16px;
    border-bottom: 2px solid var(--border);
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
  }
  thead th:hover { color: var(--primary); background: #eff6ff; }
  tbody td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-light);
    vertical-align: top;
    max-width: 300px;
    word-wrap: break-word;
  }
  tbody tr:hover { background: var(--row-hover); }
  a { color: var(--primary); font-weight: 500; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 700;
    background: #dbeafe;
    color: #1e40af;
  }
  .pagination { display: flex; align-items: center; gap: 10px; }
  .pagination select {
    height: 38px;
    background: #ffffff;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0 10px;
    font-size: 0.9rem;
  }
  .pagination button { padding: 8px 14px; font-size: 0.88rem; }
</style>
<script>window.RAW_DATA = [];</script>
__SCRIPT_TAGS__
</head>
<body>

<header>
  <div>
    <h1>VerifiedAgents — US Insurance Agents Directory</h1>
    <span class="sub">Categorize & Shortlist Agents by Location, Carrier, and Digital Presence</span>
  </div>
  <div class="actions">
    <button class="secondary" onclick="resetFilters()">Reset All Filters</button>
    <button onclick="exportFilteredCSV()">Export Filtered CSV</button>
  </div>
</header>

<div class="container">
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Total Agents</div>
      <div class="kpi-value" id="kpiTotal">0</div>
      <div class="kpi-sub">Complete dataset</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Filtered Agents</div>
      <div class="kpi-value" id="kpiFiltered" style="color:var(--green)">0</div>
      <div class="kpi-sub" id="kpiFilteredPct">0% of total</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Unique States</div>
      <div class="kpi-value" id="kpiStates" style="color:var(--purple)">0</div>
      <div class="kpi-sub">In current selection</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Unique Cities</div>
      <div class="kpi-value" id="kpiCities" style="color:var(--purple)">0</div>
      <div class="kpi-sub">In current selection</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Unique ZIP Codes</div>
      <div class="kpi-value" id="kpiZips" style="color:var(--purple)">0</div>
      <div class="kpi-sub">In current selection</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Agents with Website</div>
      <div class="kpi-value" id="kpiWeb" style="color:var(--amber)">0</div>
      <div class="kpi-sub" id="kpiWebPct">0% coverage</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Agents with Phone</div>
      <div class="kpi-value" id="kpiPhone" style="color:var(--amber)">0</div>
      <div class="kpi-sub" id="kpiPhonePct">0% coverage</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Agents with Emails</div>
      <div class="kpi-value" id="kpiEmail" style="color:var(--amber)">0</div>
      <div class="kpi-sub" id="kpiEmailPct">0% coverage</div>
    </div>
  </div>

  <div class="filter-panel">
    <div class="filter-top">
      <h2>Filter & Categorize Agents</h2>
      <span class="status-pill" id="perfBadge">Initializing...</span>
    </div>

    <div class="filter-grid">
      <div class="filter-group">
        <label for="f_state">State</label>
        <select id="f_state" onchange="onStateChange()">
          <option value="">All States</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="f_city">City</label>
        <input type="text" id="f_city" list="cityOptions" placeholder="Select or type city..." oninput="onCityInput()" />
        <datalist id="cityOptions"></datalist>
      </div>
      <div class="filter-group">
        <label for="f_zip">ZIP Code</label>
        <input type="text" id="f_zip" list="zipOptions" placeholder="Select or type ZIP..." oninput="scheduleFilter()" />
        <datalist id="zipOptions"></datalist>
      </div>
      <div class="filter-group">
        <label for="f_comp">Appointed Company</label>
        <input type="text" id="f_comp" list="companyOptions" placeholder="Select or type carrier..." oninput="scheduleFilter()" />
        <datalist id="companyOptions"></datalist>
      </div>
      <div class="filter-group">
        <label for="f_has_phone">Phone Availability</label>
        <select id="f_has_phone" onchange="applyFilters()">
          <option value="">All Agents</option>
          <option value="yes">Has Phone Number</option>
          <option value="no">No Phone Number</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="f_has_email">Email Availability</label>
        <select id="f_has_email" onchange="applyFilters()">
          <option value="">All Agents</option>
          <option value="yes">Has Email Address</option>
          <option value="no">No Email Address</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="f_has_web">Website Availability</label>
        <select id="f_has_web" onchange="applyFilters()">
          <option value="">All Agents</option>
          <option value="yes">Has Website</option>
          <option value="no">No Website</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="f_scraped">Scraped By</label>
        <select id="f_scraped" onchange="applyFilters()">
          <option value="">All Contributors</option>
        </select>
      </div>
    </div>

    <details class="advanced-drawer">
      <summary>▸ Show All Header Field Filters (Name, NPN, Street Address, Specific Contact / URL / S. No)</summary>
      <div class="filter-grid">
        <div class="filter-group">
          <label for="f_name">Full Name</label>
          <input type="text" id="f_name" placeholder="Search full name..." oninput="scheduleFilter()" />
        </div>
        <div class="filter-group">
          <label for="f_npn">NPN Number</label>
          <input type="text" id="f_npn" placeholder="Search NPN..." oninput="scheduleFilter()" />
        </div>
        <div class="filter-group">
          <label for="f_loc">Full Location / Street</label>
          <input type="text" id="f_loc" placeholder="Search street or address..." oninput="scheduleFilter()" />
        </div>
        <div class="filter-group">
          <label for="f_phone">Specific Phone / Area Code</label>
          <input type="text" id="f_phone" placeholder="e.g. (312)" oninput="scheduleFilter()" />
        </div>
        <div class="filter-group">
          <label for="f_email">Specific Email / Domain</label>
          <input type="text" id="f_email" placeholder="e.g. @statefarm.com" oninput="scheduleFilter()" />
        </div>
        <div class="filter-group">
          <label for="f_web">Specific Website URL</label>
          <input type="text" id="f_web" placeholder="Search website..." oninput="scheduleFilter()" />
        </div>
        <div class="filter-group">
          <label for="f_sno">Serial No. (Exact or Range)</label>
          <input type="text" id="f_sno" placeholder="e.g. 500 or 1-1000" oninput="scheduleFilter()" />
        </div>
        <div class="filter-group">
          <label for="f_url">Profile Page URL</label>
          <input type="text" id="f_url" placeholder="Search profile URL..." oninput="scheduleFilter()" />
        </div>
      </div>
    </details>
  </div>

  <div class="table-card">
    <div class="table-toolbar">
      <div id="tableSummary">Loading records...</div>
      <div class="pagination">
        <label for="pageSize" style="color:var(--muted)">Rows per page:</label>
        <select id="pageSize" onchange="currentPage=1; renderTable()">
          <option value="50">50</option>
          <option value="100" selected>100</option>
          <option value="250">250</option>
          <option value="500">500</option>
        </select>
        <button class="secondary" onclick="prevPage()">← Previous</button>
        <span id="pageIndicator" style="min-width:120px;text-align:center;">Page 1 of 1</span>
        <button class="secondary" onclick="nextPage()">Next →</button>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th onclick="sortBy(0)">S. No ⇅</th>
            <th onclick="sortBy(2)">Full Name ⇅</th>
            <th onclick="sortBy(3)">NPN ⇅</th>
            <th onclick="sortBy(10)">State ⇅</th>
            <th onclick="sortBy(11)">City ⇅</th>
            <th onclick="sortBy(12)">ZIP ⇅</th>
            <th onclick="sortBy(4)">Location ⇅</th>
            <th onclick="sortBy(5)">Phone Numbers ⇅</th>
            <th onclick="sortBy(6)">Email Addresses ⇅</th>
            <th onclick="sortBy(7)">Websites ⇅</th>
            <th onclick="sortBy(8)">Appointed Companies ⇅</th>
            <th onclick="sortBy(1)">Profile URL ⇅</th>
            <th onclick="sortBy(9)">Scraped By ⇅</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const STATES_LIST = __STATES__;
const SCRAPED_LIST = __SCRAPED__;
const TOP_COMPANIES = __COMPANIES__;

const SEARCH_INDEX = [];
const STATE_CITIES = {};
const STATE_CITY_ZIPS = {};

let filteredIndices = [];
let currentPage = 1;
let sortCol = 0;
let sortAsc = true;
let filterTimer = null;

function buildIndex() {
  for (let i = 0; i < window.RAW_DATA.length; i++) {
    const r = window.RAW_DATA[i];
    const st = r[10];
    const ct = r[11];
    const zp = r[12];
    if (st && ct) {
      if (!STATE_CITIES[st]) STATE_CITIES[st] = new Set();
      STATE_CITIES[st].add(ct);
      if (zp) {
        const k = st + "|" + ct.toLowerCase();
        if (!STATE_CITY_ZIPS[k]) STATE_CITY_ZIPS[k] = new Set();
        STATE_CITY_ZIPS[k].add(zp);
      }
    }
    SEARCH_INDEX.push([
      String(r[0]), r[1].toLowerCase(), r[2].toLowerCase(), r[3].toLowerCase(),
      r[4].toLowerCase(), r[5].toLowerCase(), r[6].toLowerCase(), r[7].toLowerCase(),
      r[8].toLowerCase(), r[9], st, ct.toLowerCase(), zp
    ]);
  }
}

function initDropdowns() {
  const stateSel = document.getElementById("f_state");
  STATES_LIST.forEach(st => {
    const opt = document.createElement("option");
    opt.value = st; opt.textContent = st;
    stateSel.appendChild(opt);
  });

  const scrSel = document.getElementById("f_scraped");
  SCRAPED_LIST.forEach(sc => {
    const opt = document.createElement("option");
    opt.value = sc; opt.textContent = sc;
    scrSel.appendChild(opt);
  });

  const compList = document.getElementById("companyOptions");
  TOP_COMPANIES.forEach(comp => {
    const opt = document.createElement("option");
    opt.value = comp;
    compList.appendChild(opt);
  });
}

function updateGeoDatalists() {
  const selectedState = document.getElementById("f_state").value;
  const selectedCity = document.getElementById("f_city").value.trim().toLowerCase();

  const cityList = document.getElementById("cityOptions");
  cityList.innerHTML = "";
  let cities = [];
  if (selectedState && STATE_CITIES[selectedState]) {
    cities = Array.from(STATE_CITIES[selectedState]).sort();
  } else {
    const allCities = new Set();
    Object.values(STATE_CITIES).forEach(set => {
      for (const c of set) {
        allCities.add(c);
        if (allCities.size >= 400) break;
      }
    });
    cities = Array.from(allCities).sort();
  }
  cities.slice(0, 500).forEach(c => {
    const opt = document.createElement("option");
    opt.value = c;
    cityList.appendChild(opt);
  });

  const zipList = document.getElementById("zipOptions");
  zipList.innerHTML = "";
  const key = selectedState + "|" + selectedCity;
  let zips = [];
  if (selectedState && selectedCity && STATE_CITY_ZIPS[key]) {
    zips = Array.from(STATE_CITY_ZIPS[key]).sort();
  } else if (selectedState) {
    const stZips = new Set();
    Object.entries(STATE_CITY_ZIPS).forEach(([k, set]) => {
      if (k.startsWith(selectedState + "|")) {
        for (const z of set) {
          stZips.add(z);
          if (stZips.size >= 400) break;
        }
      }
    });
    zips = Array.from(stZips).sort();
  }
  zips.slice(0, 500).forEach(z => {
    const opt = document.createElement("option");
    opt.value = z;
    zipList.appendChild(opt);
  });
}

function onStateChange() {
  updateGeoDatalists();
  applyFilters();
}

function onCityInput() {
  updateGeoDatalists();
  scheduleFilter();
}

function scheduleFilter() {
  clearTimeout(filterTimer);
  filterTimer = setTimeout(applyFilters, 180);
}

function applyFilters() {
  const t0 = performance.now();
  const fSno = document.getElementById("f_sno").value.trim();
  const fName = document.getElementById("f_name").value.trim().toLowerCase();
  const fNpn = document.getElementById("f_npn").value.trim().toLowerCase();
  const fState = document.getElementById("f_state").value;
  const fCity = document.getElementById("f_city").value.trim().toLowerCase();
  const fZip = document.getElementById("f_zip").value.trim();
  const fLoc = document.getElementById("f_loc").value.trim().toLowerCase();
  const fPhone = document.getElementById("f_phone").value.trim().toLowerCase();
  const fHasPhone = document.getElementById("f_has_phone").value;
  const fEmail = document.getElementById("f_email").value.trim().toLowerCase();
  const fHasEmail = document.getElementById("f_has_email").value;
  const fWeb = document.getElementById("f_web").value.trim().toLowerCase();
  const fHasWeb = document.getElementById("f_has_web").value;
  const fComp = document.getElementById("f_comp").value.trim().toLowerCase();
  const fUrl = document.getElementById("f_url").value.trim().toLowerCase();
  const fScraped = document.getElementById("f_scraped").value;

  let snoMin = null, snoMax = null, snoExact = null;
  if (fSno) {
    if (fSno.includes("-")) {
      const parts = fSno.split("-");
      snoMin = parseInt(parts[0], 10);
      snoMax = parseInt(parts[1], 10);
    } else {
      snoExact = fSno;
    }
  }

  const nextIndices = [];
  const statesSet = new Set();
  const citiesSet = new Set();
  const zipsSet = new Set();
  let webCount = 0, phoneCount = 0, emailCount = 0;

  for (let i = 0; i < SEARCH_INDEX.length; i++) {
    const s = SEARCH_INDEX[i];
    if (fState && s[10] !== fState) continue;
    if (fScraped && s[9] !== fScraped) continue;
    if (fHasPhone === "yes" && !s[5]) continue;
    if (fHasPhone === "no" && s[5]) continue;
    if (fHasEmail === "yes" && !s[6]) continue;
    if (fHasEmail === "no" && s[6]) continue;
    if (fHasWeb === "yes" && !s[7]) continue;
    if (fHasWeb === "no" && s[7]) continue;
    if (snoExact && s[0] !== snoExact) continue;
    if (snoMin !== null && !isNaN(snoMin) && Number(s[0]) < snoMin) continue;
    if (snoMax !== null && !isNaN(snoMax) && Number(s[0]) > snoMax) continue;
    if (fName && !s[2].includes(fName)) continue;
    if (fNpn && !s[3].includes(fNpn)) continue;
    if (fCity && !s[11].includes(fCity)) continue;
    if (fZip && !s[12].startsWith(fZip)) continue;
    if (fLoc && !s[4].includes(fLoc)) continue;
    if (fPhone && !s[5].includes(fPhone)) continue;
    if (fEmail && !s[6].includes(fEmail)) continue;
    if (fWeb && !s[7].includes(fWeb)) continue;
    if (fComp && !s[8].includes(fComp)) continue;
    if (fUrl && !s[1].includes(fUrl)) continue;

    nextIndices.push(i);
    if (s[10]) statesSet.add(s[10]);
    if (s[11]) citiesSet.add(s[10] + "|" + s[11]);
    if (s[12]) zipsSet.add(s[12]);
    if (s[7]) webCount++;
    if (s[5]) phoneCount++;
    if (s[6]) emailCount++;
  }

  filteredIndices = nextIndices;
  currentPage = 1;

  const total = window.RAW_DATA.length;
  const fCount = filteredIndices.length;
  document.getElementById("kpiTotal").textContent = total.toLocaleString();
  document.getElementById("kpiFiltered").textContent = fCount.toLocaleString();
  document.getElementById("kpiFilteredPct").textContent = total ? ((fCount / total) * 100).toFixed(1) + "% of total" : "0%";
  document.getElementById("kpiStates").textContent = statesSet.size.toLocaleString();
  document.getElementById("kpiCities").textContent = citiesSet.size.toLocaleString();
  document.getElementById("kpiZips").textContent = zipsSet.size.toLocaleString();
  document.getElementById("kpiWeb").textContent = webCount.toLocaleString();
  document.getElementById("kpiWebPct").textContent = fCount ? ((webCount / fCount) * 100).toFixed(1) + "% coverage" : "0% coverage";
  document.getElementById("kpiPhone").textContent = phoneCount.toLocaleString();
  document.getElementById("kpiPhonePct").textContent = fCount ? ((phoneCount / fCount) * 100).toFixed(1) + "% coverage" : "0% coverage";
  document.getElementById("kpiEmail").textContent = emailCount.toLocaleString();
  document.getElementById("kpiEmailPct").textContent = fCount ? ((emailCount / fCount) * 100).toFixed(1) + "% coverage" : "0% coverage";

  const elapsed = (performance.now() - t0).toFixed(0);
  document.getElementById("perfBadge").textContent = `Showing ${fCount.toLocaleString()} matching agents (${elapsed} ms)`;
  renderTable();
}

function sortBy(colIdx) {
  if (sortCol === colIdx) { sortAsc = !sortAsc; } else { sortCol = colIdx; sortAsc = true; }
  filteredIndices.sort((a, b) => {
    const va = window.RAW_DATA[a][colIdx];
    const vb = window.RAW_DATA[b][colIdx];
    if (colIdx === 0) return sortAsc ? Number(va) - Number(vb) : Number(vb) - Number(va);
    return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
  });
  currentPage = 1;
  renderTable();
}

function esc(str) {
  const d = document.createElement("div");
  d.textContent = String(str);
  return d.innerHTML;
}

function renderTable() {
  const pageSize = parseInt(document.getElementById("pageSize").value, 10);
  const total = filteredIndices.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (currentPage > totalPages) currentPage = totalPages;

  const start = (currentPage - 1) * pageSize;
  const end = Math.min(start + pageSize, total);

  document.getElementById("tableSummary").textContent =
    total === 0 ? "No matching agents found" : `Showing ${(start + 1).toLocaleString()} – ${end.toLocaleString()} of ${total.toLocaleString()} agents`;
  document.getElementById("pageIndicator").textContent = `Page ${currentPage.toLocaleString()} of ${totalPages.toLocaleString()}`;

  const tbody = document.getElementById("tableBody");
  let rowsHtml = "";
  for (let i = start; i < end; i++) {
    const r = window.RAW_DATA[filteredIndices[i]];
    const webLink = r[7] ? `<a href="${esc(r[7].split("|")[0].trim())}" target="_blank">${esc(r[7])}</a>` : "—";
    const profLink = r[1] ? `<a href="${esc(r[1])}" target="_blank">View Profile</a>` : "—";
    rowsHtml += `<tr>
      <td>${esc(r[0])}</td>
      <td><strong>${esc(r[2])}</strong></td>
      <td>${esc(r[3])}</td>
      <td>${r[10] ? `<span class="badge">${esc(r[10])}</span>` : "—"}</td>
      <td>${esc(r[11] || "—")}</td>
      <td>${esc(r[12] || "—")}</td>
      <td>${esc(r[4] || "—")}</td>
      <td>${esc(r[5] || "—")}</td>
      <td>${esc(r[6] || "—")}</td>
      <td>${webLink}</td>
      <td>${esc(r[8] || "—")}</td>
      <td>${profLink}</td>
      <td>${esc(r[9])}</td>
    </tr>`;
  }
  tbody.innerHTML = rowsHtml;
}

function prevPage() { if (currentPage > 1) { currentPage--; renderTable(); } }
function nextPage() {
  const pageSize = parseInt(document.getElementById("pageSize").value, 10);
  if (currentPage * pageSize < filteredIndices.length) { currentPage++; renderTable(); }
}
function resetFilters() {
  document.querySelectorAll(".filter-panel input").forEach(el => el.value = "");
  document.querySelectorAll(".filter-panel select").forEach(el => el.value = "");
  updateGeoDatalists();
  applyFilters();
}
function exportFilteredCSV() {
  const q = String.fromCharCode(34);
  const headers = ["s_no","profile_page_url","full_name","npn_number","state","city","zip_code","location","phone_numbers","email_addresses","websites","appointed_companies","scraped_by"];
  const rows = [headers.join(",")];
  for (let i = 0; i < filteredIndices.length; i++) {
    const r = window.RAW_DATA[filteredIndices[i]];
    const ordered = [r[0], r[1], r[2], r[3], r[10], r[11], r[12], r[4], r[5], r[6], r[7], r[8], r[9]];
    rows.push(ordered.map(v => q + String(v).split(q).join(q + q) + q).join(","));
  }
  const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `VerifiedAgents_Filtered_${filteredIndices.length}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

buildIndex();
initDropdowns();
updateGeoDatalists();
applyFilters();
</script>
</body>
</html>
"""

final_html = (
    html
    .replace("__SCRIPT_TAGS__", "\n".join(script_tags))
    .replace("__STATES__", json.dumps(states_list))
    .replace("__SCRAPED__", json.dumps(scraped_by_list))
    .replace("__COMPANIES__", json.dumps(top_companies))
)

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"Done! Created {OUTPUT_HTML} ({len(states_list)} states loaded).")
