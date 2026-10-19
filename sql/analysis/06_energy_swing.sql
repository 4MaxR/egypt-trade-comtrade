-- Q6. Egypt's energy trade: did gas (HS 2711) and oil (2709, 2710) turn from earner to cost?
SELECT
    s.year,
    s.hs4,
    d.description,
    sum(s.value_usd) FILTER (WHERE s.flow = 'export')                     AS exports_usd,
    sum(s.value_usd) FILTER (WHERE s.flow = 'import')                     AS imports_usd,
    coalesce(exports_usd, 0) - coalesce(imports_usd, 0)                   AS net_usd
FROM gold.fact_egypt_strategic AS s
JOIN gold.dim_hs4 AS d USING (hs4)
WHERE s.partner_code = 0 AND s.hs4 IN ('2709', '2710', '2711')
GROUP BY ALL
ORDER BY s.hs4, s.year;
