# VerifiedAgents_list

Pipeline and dataset tooling for collecting, auditing, and enriching US insurance producer profiles from VerifiedAgent.com and official state bulk licensing datasets.

## Dataset Coverage & Diagnostic Findings

- **VerifiedAgent Sitemap Scope:** `sitemap_index.xml` contains 660 sitemaps (~1.32M total profiles), while the initial scrape in `verifiedagents_data.db` covered `verifiedagent-agents-1.xml` through `122.xml` (243,998 records).
- **Email Availability Audit:** Inspecting empty-email profile pages confirmed that VerifiedAgent.com omits `#agent-email-addresses` on ~99.6% of profiles, explaining why direct scraping alone yielded only 891 emails.
- **Enriched Submission Dataset:** Merging `verifiedagents_data.db` with Florida Department of Financial Services (FL DFS) individual licensee bulk CSVs (`A-K` and `L-Z`, covering Florida residents and nationwide non-resident producers) deduplicated by `npn_number` produces **1,274,394 unique agents**, including **1,028,473 populated emails (80.70%)** and **1,176,637 phone numbers (92.33%)**.

## Submission Schema (10 Columns)

1. `s_no`
2. `profile_page_url`
3. `full_name`
4. `npn_number`
5. `location`
6. `phone_numbers`
7. `email_addresses`
8. `websites`
9. `appointed_companies`
10. `scraped_by`

## Usage

1. Download **All Valid Licenses - Individual (A-K)** and **All Valid Licenses - Individual (L-Z)** from the Florida DFS Bulk Download portal into `bulk_data/`.
2. Activate the virtual environment and run the merger script:
   ```bash
   source venv/bin/activate
   python3 merge_bulk_data.py