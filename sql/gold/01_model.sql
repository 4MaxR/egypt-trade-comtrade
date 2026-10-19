-- Gold: analysis-ready star schema. Values in USD; flows labelled in plain words.

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.dim_partner AS
SELECT partner_code, partner_name, iso3, is_group, is_country
FROM silver.partners;

-- HS chapter names from HS2022; chapter titles are stable between HS2012 and HS2022.
CREATE OR REPLACE TABLE gold.dim_hs2 AS
SELECT hs_code AS hs2, description
FROM silver.hs
WHERE hs_version = 'H6' AND hs_level = 2;

CREATE OR REPLACE TABLE gold.dim_hs4 AS
SELECT hs_code AS hs4, left(hs_code, 2) AS hs2, description
FROM silver.hs
WHERE hs_version = 'H6' AND hs_level = 4;

-- Egypt's own totals with the World.
CREATE OR REPLACE TABLE gold.fact_egypt_world AS
SELECT
    year,
    CASE flow WHEN 'M' THEN 'import' ELSE 'export' END AS flow,
    hs_version,
    value_usd
FROM silver.trade
WHERE source_job = 'egypt_by_partner' AND partner_code = 0;

-- Egypt's trade by partner (World row removed; statistical buckets kept but flagged in dim_partner).
CREATE OR REPLACE TABLE gold.fact_egypt_partner AS
SELECT
    year,
    partner_code,
    CASE flow WHEN 'M' THEN 'import' ELSE 'export' END AS flow,
    value_usd
FROM silver.trade
WHERE source_job = 'egypt_by_partner' AND partner_code <> 0;

-- Egypt's trade with the World by HS chapter.
CREATE OR REPLACE TABLE gold.fact_egypt_hs2 AS
SELECT
    year,
    cmd_code AS hs2,
    CASE flow WHEN 'M' THEN 'import' ELSE 'export' END AS flow,
    hs_version,
    value_usd
FROM silver.trade
WHERE source_job = 'egypt_by_hs2';

-- Strategic HS4 headings by partner; partner_code 0 rows are the World totals.
CREATE OR REPLACE TABLE gold.fact_egypt_strategic AS
SELECT
    year,
    cmd_code AS hs4,
    partner_code,
    CASE flow WHEN 'M' THEN 'import' ELSE 'export' END AS flow,
    value_usd,
    net_weight_kg
FROM silver.trade
WHERE source_job = 'egypt_strategic_hs4';

-- Mirror comparison: each bilateral flow as Egypt records it vs as the partner records it.
-- Egypt's imports from P (CIF) are matched with P's exports to Egypt (FOB), and vice versa.
-- Only partners that report to Comtrade themselves (non-group reporters) appear.
CREATE OR REPLACE TABLE gold.fact_mirror AS
WITH egypt AS (
    SELECT year, partner_code AS counterpart_code, flow, value_usd
    FROM silver.trade
    WHERE source_job = 'egypt_by_partner' AND partner_code <> 0
),
partner AS (
    SELECT t.year, t.reporter_code AS counterpart_code,
           CASE t.flow WHEN 'X' THEN 'M' ELSE 'X' END AS flow,   -- partner export = Egypt import
           t.value_usd
    FROM silver.trade AS t
    JOIN silver.reporters AS r USING (reporter_code)
    WHERE t.source_job = 'mirror_partners' AND NOT r.is_group
)
SELECT
    p.year,
    p.counterpart_code AS partner_code,
    CASE p.flow WHEN 'M' THEN 'import' ELSE 'export' END AS egypt_flow,
    e.value_usd AS egypt_reported_usd,
    p.value_usd AS partner_reported_usd
FROM partner AS p
LEFT JOIN egypt AS e USING (year, counterpart_code, flow);
