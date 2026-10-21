# Cleaning log

Raw rows: 242,580

- Dropped 198 exact duplicate rows.
- Fixed 157 rows with boro = '0' -> 'Unknown'.
- Normalized grades: only A/B/C kept; N/Z/P/blank -> null
  (41,456 of 69,156 inspections are graded).
- Scores: blanks kept null (unscored inspection types); range in cleaned
  data 0–214, lower is better.
- Violations table: 239,626 rows (real violation codes only).
- Inspections table: 69,156 rows (one per camis + date), covering
  27,067 distinct restaurants.
- Inspections with zero violations: 2,551.
