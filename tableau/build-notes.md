# Tableau build notes — NYC Restaurant Inspections dashboard

Data sources (Tableau can join or use separately):
- `data/cleaned/inspections.csv` — main source (one row per inspection)
- `data/cleaned/violations.csv` — for the violations chart

## Page layout (one dashboard page)

1. **KPI row (4 tiles)**: restaurants inspected (COUNTD of camis), total
   inspections, % of graded inspections that are A, average score.
2. **Map** — one point per inspection (latitude/longitude), sized or colored
   by score. Filter to a single borough to keep it readable.
3. **Grade mix by borough** — stacked bar: A / B / C share per borough
   (filter `grade` to A, B, C only — nulls are ungraded inspections).
4. **Top 10 violations** — bar chart from `violations.csv`, COUNT of rows
   by violation_code, label with the description.
5. **Trend line** — inspections per month (`inspection_date` by month).

## Tableau skills this practices

- Connecting two CSVs and checking data types on import
  (`inspection_date` = date, `score` = number, lat/long = geographic role)
- COUNTD for distinct restaurants
- Calculated field for % A: `SUM(IF [Grade]='A' THEN 1 ELSE 0 END) / COUNT of graded`
- Stacked bar with a dimension on Color
- Map with lat/long (assign Geographic Role if Tableau doesn't pick it up)
- Filters: borough filter applied to all sheets (dashboard filter action)

## Gotchas

- **Null grades are not "bad" grades** — they're ungraded/pending inspections.
  Exclude them from the grade chart or you'll invent a giant "blank" category.
- **Score is backwards**: lower = cleaner. Say so in the chart title or
  subtitle ("avg score — lower is better") so nobody misreads it.
- The map will try to plot a few inspections with missing lat/long — filter
  nulls out.
