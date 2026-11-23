import glob, sqlite3
import pandas as pd

DB_PATH = "verifiedagents_data.db"
BULK_FILES = sorted(glob.glob("bulk_data/*.csv"))
OUT_CSV = "VerifiedAgents_Submission_Full.csv"
SCRAPED_BY = "Dhruv Shetty"

def find_col(cols, *keywords):
    for col in cols:
        low = col.lower()
        if all(k in low for k in keywords):
            return col
    return None

with sqlite3.connect(DB_PATH) as conn:
    va_df = pd.read_sql_query("""
        SELECT profile_page_url, full_name, npn_number, location,
               phone_numbers, email_addresses, websites, appointed_companies,
               scraped_by
        FROM agents
    """, conn)

va_df["npn_number"] = va_df["npn_number"].astype(str).str.strip()
print(f"Existing DB: {len(va_df):,} rows | Emails: {(va_df['email_addresses'] != '').sum():,}")

fl_frames = []
for path in BULK_FILES:
    if "appointment" in path.lower():
        continue
    print(f"Reading {path} ...")
    df = pd.read_csv(path, dtype=str, low_memory=False).fillna("")
    cols = list(df.columns)

    c_npn = find_col(cols, "npn")
    c_full = find_col(cols, "full", "name") or find_col(cols, "licensee", "name")
    c_first = find_col(cols, "first", "name")
    c_last = find_col(cols, "last", "name")
    c_email = find_col(cols, "email")
    c_phone = find_col(cols, "business", "phone") or find_col(cols, "phone")
    c_city = find_col(cols, "business", "city") or find_col(cols, "city")
    c_state = find_col(cols, "business", "state") or find_col(cols, "state")
    c_zip = find_col(cols, "business", "zip") or find_col(cols, "zip")

    if not c_npn:
        print(f"Skipping {path} (no NPN column). Columns: {cols[:10]}")
        continue

    out = pd.DataFrame()
    out["npn_number"] = df[c_npn].str.strip()
    if c_full:
        out["full_name"] = df[c_full].str.strip()
    elif c_first and c_last:
        out["full_name"] = (df[c_first].str.strip() + " " + df[c_last].str.strip()).str.strip()
    else:
        out["full_name"] = ""

    loc_parts = [df[c].str.strip() for c in (c_city, c_state, c_zip) if c]
    out["location"] = pd.concat(loc_parts, axis=1).agg(lambda r: ", ".join([x for x in r if x]), axis=1) if loc_parts else ""
    out["phone_numbers"] = df[c_phone].str.strip() if c_phone else ""
    out["email_addresses"] = df[c_email].str.strip() if c_email else ""
    out["profile_page_url"] = "https://licenseesearch.fldfs.com/"
    out["websites"] = ""
    out["appointed_companies"] = ""
    out["scraped_by"] = SCRAPED_BY

    out = out[out["npn_number"] != ""].drop_duplicates(subset=["npn_number"])
    fl_frames.append(out)

fl_df = pd.concat(fl_frames, ignore_index=True).drop_duplicates(subset=["npn_number"])
print(f"Florida DFS unique producers: {len(fl_df):,} rows | Emails: {(fl_df['email_addresses'] != '').sum():,}")

merged = pd.merge(va_df, fl_df, on="npn_number", how="outer", suffixes=("_va", "_fl")).fillna("")

final = pd.DataFrame()
for col in ["profile_page_url", "full_name", "location", "phone_numbers", "email_addresses", "websites", "appointed_companies"]:
    final[col] = merged[f"{col}_va"].where(merged[f"{col}_va"] != "", merged[f"{col}_fl"])

final["npn_number"] = merged["npn_number"]
final["scraped_by"] = SCRAPED_BY
final = final.sort_values("npn_number").reset_index(drop=True)
final.insert(0, "s_no", range(1, len(final) + 1))

target_columns = [
    "s_no", "profile_page_url", "full_name", "npn_number",
    "location", "phone_numbers", "email_addresses", "websites",
    "appointed_companies", "scraped_by"
]
final = final[target_columns]
final.to_csv(OUT_CSV, index=False)
print(f"DONE -> {OUT_CSV} | Total unique agents: {len(final):,} | Total emails: {(final['email_addresses'] != '').sum():,}")
