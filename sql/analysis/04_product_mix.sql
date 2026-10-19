-- Q4. What does Egypt trade? Top 10 HS chapters per flow by cumulative value, every year.
WITH ranked AS (
    SELECT flow, hs2,
           row_number() OVER (PARTITION BY flow ORDER BY sum(value_usd) DESC) AS rank_overall
    FROM gold.fact_egypt_hs2
    GROUP BY flow, hs2
)
SELECT
    f.year,
    f.flow,
    r.rank_overall,
    f.hs2,
    d.description,
    f.value_usd,
    f.value_usd / w.value_usd AS share_of_total
FROM gold.fact_egypt_hs2 AS f
JOIN ranked AS r USING (flow, hs2)
JOIN gold.dim_hs2 AS d USING (hs2)
JOIN gold.fact_egypt_world AS w USING (year, flow)
WHERE r.rank_overall <= 10
ORDER BY f.flow, f.year, r.rank_overall;
