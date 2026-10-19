-- Q1. How did Egypt's imports, exports and trade deficit move from 2014 to 2025?
SELECT
    year,
    max(hs_version)                                             AS hs_version,
    sum(value_usd) FILTER (WHERE flow = 'import')               AS imports_usd,
    sum(value_usd) FILTER (WHERE flow = 'export')               AS exports_usd,
    exports_usd - imports_usd                                   AS balance_usd,
    exports_usd / imports_usd                                   AS export_coverage_ratio,
    imports_usd / lag(imports_usd) OVER (ORDER BY year) - 1     AS imports_yoy,
    exports_usd / lag(exports_usd) OVER (ORDER BY year) - 1     AS exports_yoy
FROM gold.fact_egypt_world
GROUP BY year
ORDER BY year;
