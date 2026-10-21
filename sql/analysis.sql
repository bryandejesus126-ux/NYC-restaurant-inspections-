-- NYC Restaurant Inspections — starter SQL (beginner)
--
-- Two tables (see data/cleaned/):
--   inspections: camis, dba, boro, zipcode, cuisine, inspection_date,
--                inspection_type, score, grade, latitude, longitude,
--                violation_count, critical_count
--   violations:  camis, dba, boro, zipcode, cuisine, inspection_date,
--                violation_code, violation_description, critical_flag,
--                score, grade, inspection_type
--
-- Remember: score — LOWER is better. Grade A = 0-13 pts, B = 14-27, C = 28+.

-- Q1: Grade distribution — what % of graded inspections get an A, B, or C?
SELECT grade,
       COUNT(*) AS inspections,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM inspections
WHERE grade IS NOT NULL
GROUP BY grade
ORDER BY grade;

-- Q2: Average score by borough (scored inspections only)
SELECT boro,
       COUNT(*) AS inspections,
       ROUND(AVG(score), 1) AS avg_score
FROM inspections
WHERE score IS NOT NULL AND boro <> 'Unknown'
GROUP BY boro
ORDER BY avg_score DESC;

-- Q3: Clean inspections — % with zero violations, by borough
SELECT boro,
       COUNT(*) AS inspections,
       ROUND(100.0 * SUM(CASE WHEN violation_count = 0 THEN 1 ELSE 0 END) / COUNT(*), 1)
           AS pct_zero_violations
FROM inspections
WHERE boro <> 'Unknown'
GROUP BY boro
ORDER BY pct_zero_violations DESC;

-- Q4: The 10 most common violations — and how many are critical
SELECT violation_code,
       violation_description,
       COUNT(*) AS times_cited,
       SUM(CASE WHEN critical_flag = 'Critical' THEN 1 ELSE 0 END) AS critical_citations
FROM violations
GROUP BY violation_code, violation_description
ORDER BY times_cited DESC
LIMIT 10;

-- Q5: Worst cuisines by average score (at least 100 inspections, so
--     one tiny category can't top the list by luck)
SELECT cuisine,
       COUNT(*) AS inspections,
       ROUND(AVG(score), 1) AS avg_score,
       ROUND(AVG(critical_count), 2) AS avg_critical_per_inspection
FROM inspections
WHERE score IS NOT NULL
GROUP BY cuisine
HAVING COUNT(*) >= 100
ORDER BY avg_score DESC
LIMIT 10;

-- Q6: Repeat offenders — restaurants with the most critical violations
SELECT camis, dba, boro, cuisine,
       COUNT(DISTINCT inspection_date) AS inspections,
       SUM(critical_count) AS total_critical_violations,
       ROUND(AVG(score), 1) AS avg_score
FROM inspections
GROUP BY camis, dba, boro, cuisine
ORDER BY total_critical_violations DESC
LIMIT 10;

-- Q7: Inspections per month, 2024 -> 2026
SELECT SUBSTR(inspection_date, 1, 7) AS month,
       COUNT(*) AS inspections
FROM inspections
GROUP BY month
ORDER BY month;

-- Q8 (window function): rank boroughs by avg score within each year
WITH yearly AS (
    SELECT SUBSTR(inspection_date, 1, 4) AS yr, boro,
           ROUND(AVG(score), 1) AS avg_score
    FROM inspections
    WHERE score IS NOT NULL AND boro <> 'Unknown'
    GROUP BY yr, boro
)
SELECT yr, boro, avg_score,
       RANK() OVER (PARTITION BY yr ORDER BY avg_score DESC) AS worst_rank
FROM yearly
ORDER BY yr, worst_rank;
