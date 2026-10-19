-- Q7. Do Egypt's customs records agree with its partners' records of the same trade?
-- Egypt's imports are valued CIF and partner exports FOB, so a ratio of roughly 1.05-1.10 is
-- normal freight and insurance. Far outside that band points to misclassification, transit
-- routing, timing or valuation issues worth a customs analyst's attention.
-- Year fixed at 2023: the latest year in which most partners have reported.
SELECT
    m.year,
    p.partner_name,
    m.egypt_flow,
    m.egypt_reported_usd,
    m.partner_reported_usd,
    m.egypt_reported_usd - m.partner_reported_usd   AS gap_usd,
    m.egypt_reported_usd / m.partner_reported_usd   AS egypt_to_partner_ratio
FROM gold.fact_mirror AS m
JOIN gold.dim_partner AS p USING (partner_code)
WHERE m.year = 2023
  AND p.is_country
  AND greatest(coalesce(m.egypt_reported_usd, 0), m.partner_reported_usd) >= 1e9
ORDER BY abs(gap_usd) DESC;
