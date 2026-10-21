"""Clean the raw NYC restaurant inspection CSV into two analysis tables.

Usage: python3 clean.py    (run from this scripts/ folder)

Outputs (in ../data/cleaned/):
  violations.csv   — one row per violation cited
  inspections.csv  — one row per inspection (camis + inspection_date)
  cleaning_notes.md — what was changed and why

Decisions (see README for the full reasoning):
  1. Drop exact duplicate rows (198 in the raw file).
  2. boro '0' (157 rows) -> 'Unknown'.
  3. Grades N / Z / P / blank are administrative states, not grades -> null.
     Only A / B / C count as graded.
  4. Blank score stays null (unscored inspection types); never zero-fill —
     0 is a real, perfect score.
  5. violations grain = rows with a real violation_code. No-violation
     inspections appear only in the inspections table (violation_count = 0).
  6. DBA names: trim + collapse whitespace (source is ALL CAPS; kept as-is).
"""
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw", "inspections_raw.csv")
OUT = os.path.join(BASE, "data", "cleaned")
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(RAW, dtype=str, low_memory=False)
n_raw = len(df)

# 1. Exact duplicates
df = df.drop_duplicates()
n_dupes = n_raw - len(df)

# Types + dates
df["inspection_date"] = pd.to_datetime(df["inspection_date"]).dt.strftime("%Y-%m-%d")
df["score"] = pd.to_numeric(df["score"], errors="coerce").astype("Int64")
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

# 2. Borough junk value
n_boro_fixed = (df["boro"] == "0").sum()
df.loc[df["boro"] == "0", "boro"] = "Unknown"

# 6. Name whitespace
df["dba"] = df["dba"].str.strip().str.replace(r"\s+", " ", regex=True)

# 3. Grade normalization
df["grade"] = df["grade"].where(df["grade"].isin(["A", "B", "C"]))

df = df.rename(columns={"cuisine_description": "cuisine"})

# --- violations grain (rows with a real violation code) ---
viol = df[df["violation_code"].notna() & (df["violation_code"].str.strip() != "")].copy()
viol_cols = ["camis", "dba", "boro", "zipcode", "cuisine", "inspection_date",
             "violation_code", "violation_description", "critical_flag",
             "score", "grade", "inspection_type"]
viol[viol_cols].to_csv(os.path.join(OUT, "violations.csv"), index=False)

# --- inspections grain (one row per camis + date) ---
def first_non_null(s):
    s = s.dropna()
    return s.iloc[0] if len(s) else None

insp = (
    df.groupby(["camis", "inspection_date"], as_index=False)
      .agg(dba=("dba", "first"),
           boro=("boro", "first"),
           zipcode=("zipcode", "first"),
           cuisine=("cuisine", "first"),
           inspection_type=("inspection_type", "first"),
           score=("score", "max"),
           grade=("grade", first_non_null),
           latitude=("latitude", "max"),
           longitude=("longitude", "max"),
           violation_count=("violation_code", "count"),
           critical_count=("critical_flag", lambda s: (s == "Critical").sum()))
)
insp.to_csv(os.path.join(OUT, "inspections.csv"), index=False)

notes = f"""# Cleaning log

Raw rows: {n_raw:,}

- Dropped {n_dupes} exact duplicate rows.
- Fixed {n_boro_fixed} rows with boro = '0' -> 'Unknown'.
- Normalized grades: only A/B/C kept; N/Z/P/blank -> null
  ({insp['grade'].notna().sum():,} of {len(insp):,} inspections are graded).
- Scores: blanks kept null (unscored inspection types); range in cleaned
  data {int(insp['score'].min())}–{int(insp['score'].max())}, lower is better.
- Violations table: {len(viol):,} rows (real violation codes only).
- Inspections table: {len(insp):,} rows (one per camis + date), covering
  {insp['camis'].nunique():,} distinct restaurants.
- Inspections with zero violations: {(insp['violation_count'] == 0).sum():,}.
"""
with open(os.path.join(OUT, "cleaning_notes.md"), "w") as fh:
    fh.write(notes)
print(notes)
