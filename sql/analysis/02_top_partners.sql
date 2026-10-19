-- Q2. Who does Egypt buy from and sell to, and how did each partner's share change?
-- Top 8 countries per flow by cumulative 2014-2025 value; shares are of the World total.
WITH ranked AS (
    SELECT flow, partner_code,
           row_number() OVER (PARTITION BY flow ORDER BY sum(value_usd) DESC) AS rank_overall
    FROM gold.fact_egypt_partner
    JOIN gold.dim_partner USING (partner_code)
    WHERE is_country
    GROUP BY flow, partner_code
)
SELECT
    f.year,
    f.flow,
    r.rank_overall,
    p.partner_name,
    f.value_usd,
    f.value_usd / w.value_usd AS share_of_total
FROM gold.fact_egypt_partner AS f
JOIN ranked AS r USING (flow, partner_code)
JOIN gold.dim_partner AS p USING (partner_code)
JOIN gold.fact_egypt_world AS w USING (year, flow)
WHERE r.rank_overall <= 8
ORDER BY f.flow, f.year, r.rank_overall;
