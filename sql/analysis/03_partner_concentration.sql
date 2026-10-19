-- Q3. Is Egypt's trade becoming more or less dependent on a few partners?
-- HHI on country shares (0-10,000; above 1,500 is "moderately concentrated" in antitrust terms).
WITH shares AS (
    SELECT
        f.year, f.flow, p.partner_name,
        f.value_usd / sum(f.value_usd) OVER (PARTITION BY f.year, f.flow) AS share
    FROM gold.fact_egypt_partner AS f
    JOIN gold.dim_partner AS p USING (partner_code)
    WHERE p.is_country AND f.value_usd > 0
),
ranked AS (
    SELECT *, row_number() OVER (PARTITION BY year, flow ORDER BY share DESC) AS rnk
    FROM shares
)
SELECT
    year,
    flow,
    count(*)                                     AS partner_countries,
    round(sum(power(share * 100, 2)))            AS hhi,
    max(share)                                   AS top1_share,
    arg_max(partner_name, share)                 AS top1_partner,
    sum(share) FILTER (WHERE rnk <= 5)           AS top5_share
FROM ranked
GROUP BY year, flow
ORDER BY flow, year;
