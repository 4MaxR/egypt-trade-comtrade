-- Q7b. The same mirror comparison summed over every partner that reports, by year.
-- Pairs where only one side reported are excluded so both totals cover the same partners.
SELECT
    m.year,
    m.egypt_flow,
    count(*)                                         AS matched_partners,
    sum(m.egypt_reported_usd)                        AS egypt_reported_usd,
    sum(m.partner_reported_usd)                      AS partner_reported_usd,
    sum(m.egypt_reported_usd) / sum(m.partner_reported_usd) AS egypt_to_partner_ratio
FROM gold.fact_mirror AS m
JOIN gold.dim_partner AS p USING (partner_code)
WHERE p.is_country AND m.egypt_reported_usd IS NOT NULL
GROUP BY m.year, m.egypt_flow
ORDER BY m.egypt_flow, m.year;
