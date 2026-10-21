"""Run the analysis queries against the cleaned tables and save results.

Usage: python3 run_analysis.py   (run from this scripts/ folder)

Loads data/cleaned/*.csv into SQLite (in-memory), runs the questions from
../sql/analysis.sql, saves each result as a CSV in ../results/, and prints
the headline findings.
"""
import csv
import os
import sqlite3

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(BASE, "results")
os.makedirs(RESULTS, exist_ok=True)

con = sqlite3.connect(":memory:")
cur = con.cursor()

TABLES = {
    "inspections": ["camis", "inspection_date", "dba", "boro", "zipcode", "cuisine",
                    "inspection_type", "score", "grade", "latitude", "longitude",
                    "violation_count", "critical_count"],
    "violations": ["camis", "dba", "boro", "zipcode", "cuisine", "inspection_date",
                   "violation_code", "violation_description", "critical_flag",
                   "score", "grade", "inspection_type"],
}
for name, cols in TABLES.items():
    cur.execute(f"CREATE TABLE {name} ({', '.join(c + ' TEXT' for c in cols)})")
    with open(os.path.join(BASE, "data", "cleaned", f"{name}.csv")) as fh:
        rows = [[r[c] if r[c] != "" else None for c in cols] for r in csv.DictReader(fh)]
    cur.executemany(f"INSERT INTO {name} VALUES ({','.join('?' * len(cols))})", rows)
for int_col in ("score", "violation_count", "critical_count"):
    cur.execute(f"UPDATE inspections SET {int_col} = CAST({int_col} AS INTEGER) "
                f"WHERE {int_col} IS NOT NULL")
cur.execute("UPDATE violations SET score = CAST(score AS INTEGER) WHERE score IS NOT NULL")
con.commit()

QUERIES = {
    "grade_distribution": """
        SELECT grade, COUNT(*) AS inspections,
               ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) AS pct
        FROM inspections WHERE grade IS NOT NULL GROUP BY grade ORDER BY grade""",
    "avg_score_by_borough": """
        SELECT boro, COUNT(*) AS inspections, ROUND(AVG(score),1) AS avg_score
        FROM inspections WHERE score IS NOT NULL AND boro <> 'Unknown'
        GROUP BY boro ORDER BY avg_score DESC""",
    "clean_inspections_by_borough": """
        SELECT boro, COUNT(*) AS inspections,
               ROUND(100.0*SUM(CASE WHEN violation_count=0 THEN 1 ELSE 0 END)/COUNT(*),1)
                   AS pct_zero_violations
        FROM inspections WHERE boro <> 'Unknown'
        GROUP BY boro ORDER BY pct_zero_violations DESC""",
    "top_violations": """
        SELECT violation_code, violation_description, COUNT(*) AS times_cited,
               SUM(CASE WHEN critical_flag='Critical' THEN 1 ELSE 0 END) AS critical_citations
        FROM violations GROUP BY violation_code, violation_description
        ORDER BY times_cited DESC LIMIT 10""",
    "worst_cuisines": """
        SELECT cuisine, COUNT(*) AS inspections, ROUND(AVG(score),1) AS avg_score,
               ROUND(AVG(critical_count),2) AS avg_critical_per_inspection
        FROM inspections WHERE score IS NOT NULL GROUP BY cuisine
        HAVING COUNT(*) >= 100 ORDER BY avg_score DESC LIMIT 10""",
    "repeat_offenders": """
        SELECT camis, dba, boro, cuisine, COUNT(DISTINCT inspection_date) AS inspections,
               SUM(critical_count) AS total_critical_violations, ROUND(AVG(score),1) AS avg_score
        FROM inspections GROUP BY camis, dba, boro, cuisine
        ORDER BY total_critical_violations DESC LIMIT 10""",
    "inspections_per_month": """
        SELECT SUBSTR(inspection_date,1,7) AS month, COUNT(*) AS inspections
        FROM inspections GROUP BY month ORDER BY month""",
}

for name, q in QUERIES.items():
    rows = cur.execute(q).fetchall()
    cols = [d[0] for d in cur.description]
    with open(os.path.join(RESULTS, f"{name}.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print(f"== {name} ==")
    print(", ".join(cols))
    for r in rows[:6]:
        print(r)
    print()
