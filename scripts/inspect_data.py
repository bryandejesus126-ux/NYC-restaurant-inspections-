"""Starter: profile the raw NYC restaurant inspection CSV.

Usage: python3 inspect_data.py    (run from this scripts/ folder)

Prints row/column counts, blank rates, the weird values hiding in key
columns, and the grain of the data (rows vs inspections vs restaurants).
"""
import os
import pandas as pd

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "inspections_raw.csv")

df = pd.read_csv(RAW, dtype=str, low_memory=False)
print(f"Rows: {len(df):,}   Columns: {len(df.columns)}")

print("\nBlank/missing rate by column:")
for c in df.columns:
    blank = df[c].isna() | (df[c].str.strip() == "")
    if blank.any():
        print(f"  {c}: {blank.mean():.1%}")

print("\nBoro values:", df["boro"].value_counts(dropna=False).to_dict())
print("Grade values:", df["grade"].value_counts(dropna=False).to_dict())
print("Critical flag:", df["critical_flag"].value_counts(dropna=False).to_dict())
print(f"\nExact duplicate rows: {df.duplicated().sum():,}")
print(f"Distinct restaurants (camis): {df['camis'].nunique():,}")
print(f"Distinct inspections (camis + date): "
      f"{df.drop_duplicates(['camis', 'inspection_date']).shape[0]:,}")
print(f"Date range: {df['inspection_date'].min()} -> {df['inspection_date'].max()}")
print("\nNext: run clean.py — the README explains the decisions it makes.")
