-- Q5. Where does the world's largest wheat buyer get its wheat (HS 1001), before and after 2022?
-- Origins outside the top 6 (by cumulative value) are grouped as "Other".
-- Values only: Comtrade's net weights here are largely imputed (one identical USD/tonne for
-- every origin in a year), so tonnage and unit prices are not reported.
WITH wheat AS (
    SELECT s.year, s.partner_code, p.partner_name, s.value_usd
    FROM gold.fact_egypt_strategic AS s
    JOIN gold.dim_partner AS p USING (partner_code)
    WHERE s.hs4 = '1001' AND s.flow = 'import' AND s.partner_code <> 0
),
top_origins AS (
    SELECT partner_code
    FROM wheat
    GROUP BY partner_code
    ORDER BY sum(value_usd) DESC
    LIMIT 6
),
labelled AS (
    SELECT
        w.*,
        CASE WHEN t.partner_code IS NOT NULL THEN w.partner_name ELSE 'Other' END AS origin
    FROM wheat AS w
    LEFT JOIN top_origins AS t USING (partner_code)
)
SELECT
    year,
    origin,
    sum(value_usd)                                                 AS value_usd,
    sum(value_usd) / sum(sum(value_usd)) OVER (PARTITION BY year)  AS share
FROM labelled
GROUP BY year, origin
ORDER BY year, value_usd DESC;
