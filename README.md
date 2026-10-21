# NYC Restaurant Inspections — Data Project

An entry-level, end-to-end analytics project on **New York City restaurant
health inspections** (NYC Open Data / DOHMH). One messy real-world dataset,
three skills practiced in sequence: data cleansing → SQL → Tableau.

**Headline shape of the data:** 242,580 violation rows, covering 69,156
inspections at 27,067 restaurants, Jan 2024 – Oct 2026.

## The skill roadmap

| Step | Skill | What you'll do |
|------|-------|----------------|
| 1. Get the data | — | Download from the NYC Open Data API (already in `data/raw/`) |
| 2. Profile & clean | Data cleansing | Inspect the raw CSV → fix bad boroughs, dedupe, split one file into two tables at different grains |
| 3. Load & analyze | SQL | Answer questions with aggregations, `CASE`, ranking — grade distribution, worst cuisines, repeat offenders |
| 4. Visualize | Tableau | One-page dashboard: map + grade bars + violation chart + trend |

## Step 1 — Get the data

Source: [DOHMH Restaurant Inspection Results](https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j)
on NYC Open Data (Socrata API, no key needed).

The raw file (`data/raw/inspections_raw.csv`, ~101 MB) is **not** committed to
git — re-download it any time:

```bash
# 242,580 rows, inspections since 2024-01-01, in 50k-row pages
for off in 0 50000 100000 150000 200000; do
  curl -s -G "https://data.cityofnewyork.us/resource/43nn-pn8j.csv" \
    --data-urlencode '$select=camis,dba,boro,building,street,zipcode,cuisine_description,inspection_date,action,violation_code,violation_description,critical_flag,score,grade,inspection_type,latitude,longitude' \
    --data-urlencode "\$where=inspection_date >= '2024-01-01T00:00:00'" \
    --data-urlencode '$order=camis, inspection_date, violation_code' \
    --data-urlencode '$limit=50000' --data-urlencode "\$offset=$off"
done
```

(Concatenate the pages, keeping one header row.)

## The data model (the key insight)

**One row = one violation** cited at one inspection. That's not the grain you
always want, so cleaning produces **two tables**:

| Table | Grain | Rows |
|-------|-------|------|
| `violations.csv` | one row per violation | ~241k |
| `inspections.csv` | one row per inspection (`camis` + date) | ~69k |

Key fields:

| Field | Meaning |
|-------|---------|
| `camis` | Restaurant ID (the same restaurant keeps its `camis` across inspections) |
| `dba` | "Doing business as" — restaurant name, ALL CAPS in the raw file |
| `boro` | Borough — including 157 junk rows where it's literally `0` |
| `cuisine_description` | Cuisine category (American, Chinese, Pizza, ...) |
| `inspection_date` | Date of the inspection |
| `violation_code` / `violation_description` | What was cited (blank = no violation found) |
| `critical_flag` | `Critical` violations are the serious ones (food safety risk) |
| `score` | Inspection score — **lower is better**. 0 = perfect |
| `grade` | A (0–13 pts), B (14–27), C (28+). Blank/`N`/`Z`/`P` = not a real grade (pending / not yet graded) |

## Cleaning decisions (documented in `data/cleaned/cleaning_notes.md`)

- **198 exact duplicate rows** in the raw file → dropped.
- **`boro = '0'`** (157 rows) → set to `Unknown`.
- **Grade blanks and codes `N`/`Z`/`P`** are administrative states, not grades
  → normalized to null; only `A`/`B`/`C` count as graded.
- **`score` blank on 4.7% of rows** — some inspection types aren't scored →
  kept null, never zero-filled (a fake 0 would look like a perfect score).
- **No-violation inspections** have one row with blank `violation_code` →
  they belong in `inspections` (with `violation_count = 0`), not `violations`.
- **Two grains**: `violations` keeps rows with a real `violation_code`;
  `inspections` rolls each `camis` + date up to one row with counts.

## Analysis questions (SQL — see `sql/analysis.sql`)

1. What % of graded inspections earn an A, B, or C?
2. Which borough has the worst average score?
3. What % of inspections find zero violations — by borough?
4. What are the 10 most common violations? How many are critical?
5. Which cuisines have the worst average scores (min 100 inspections)?
6. Who are the repeat offenders — restaurants with the most critical violations?
7. How have inspection counts trended month over month, 2024 → 2026?

## Findings (Jan 2024 – Oct 2026, from `results/`)

- **Most restaurants pass well**: of 41,456 graded inspections, **87.1% earned
  an A**, 8.4% a B, and only 4.5% a C.
- **Queens has the worst average score** (19.6); Staten Island the best (17.0).
  Manhattan has the most inspections (25,954) and the highest share of
  zero-violation inspections (4.8%).
- **A perfectly clean inspection is rare**: only 2,551 of 69,156 inspections
  (3.7%) found zero violations.
- **Most common violation overall**: 10F — non-food contact surfaces/equipment
  not kept clean (34,169 citations, non-critical). The most common *critical*
  violations are food-safety basics: cold food held above safe temperature
  (02G, 16,088), food not protected from contamination (06C, 16,085), and
  food-contact surfaces not sanitized (06D, 15,230).
- **Worst cuisine by average score**: Bangladeshi (31.2 — C-grade territory),
  then African (25.6) and Filipino (25.0).
- **Worst repeat offender**: BYUNG CHUN SOON DAE (Korean, Queens) — 58 critical
  violations across 10 inspections, average score 49.4.

## Tableau dashboard (one page — see `tableau/build-notes.md`)

- **KPI row**: restaurants inspected, total inspections, % A grades, avg score
- **Map**: inspections by ZIP code (lat/long points, sized by count)
- **Stacked bar**: grade mix (A/B/C) by borough
- **Bar**: top 10 violation codes
- **Line**: inspections per month

## How to reproduce

```bash
python3 scripts/inspect_data.py   # profile the raw file
python3 scripts/clean.py          # raw -> data/cleaned/ (two tables)
python3 scripts/run_analysis.py   # cleaned -> results/ (SQLite in-memory)
```

## Folder layout

```
nyc-restaurant-inspections/
├── README.md
├── data/
│   ├── raw/          <- inspections_raw.csv (gitignored, ~101 MB)
│   └── cleaned/      <- violations.csv, inspections.csv, cleaning_notes.md
├── scripts/
│   ├── inspect_data.py
│   ├── clean.py
│   └── run_analysis.py
├── sql/
│   └── analysis.sql
├── results/          <- one CSV per query
└── tableau/
    └── build-notes.md
```
