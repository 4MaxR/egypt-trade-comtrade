-- Silver: typed, renamed, de-duplicated records and clean reference dimensions.

CREATE SCHEMA IF NOT EXISTS silver;

-- One row per (job, year, reporter, partner, flow, commodity). Only the plain totals are kept:
-- all customs procedures (C00), all transport modes (0), no second partner (0).
CREATE OR REPLACE TABLE silver.trade AS
SELECT DISTINCT ON (_job, refYear, reporterCode, partnerCode, flowCode, cmdCode)
    _job                               AS source_job,
    CAST(refYear AS SMALLINT)          AS year,
    CAST(reporterCode AS INTEGER)      AS reporter_code,
    CAST(partnerCode AS INTEGER)       AS partner_code,
    CAST(flowCode AS VARCHAR)          AS flow,          -- M = import, X = export
    CAST(cmdCode AS VARCHAR)           AS cmd_code,      -- TOTAL, HS2 chapter or HS4 heading
    CAST(classificationCode AS VARCHAR) AS hs_version,   -- H4 = HS2012, H6 = HS2022
    CAST(primaryValue AS DOUBLE)       AS value_usd,     -- CIF for imports, FOB for exports
    CAST(cifvalue AS DOUBLE)           AS cif_usd,
    CAST(fobvalue AS DOUBLE)           AS fob_usd,
    NULLIF(CAST(netWgt AS DOUBLE), 0)  AS net_weight_kg, -- sparsely reported; NULL when missing
    CAST(isReported AS BOOLEAN)        AS is_reported,
    CAST(_extracted_at AS TIMESTAMPTZ) AS extracted_at
FROM bronze.comtrade_records
WHERE customsCode = 'C00'
  AND CAST(motCode AS INTEGER) = 0
  AND CAST(partner2Code AS INTEGER) = 0
ORDER BY _job, refYear, reporterCode, partnerCode, flowCode, cmdCode, _extracted_at DESC;

-- Partner areas. Comtrade mixes real economies with statistical buckets
-- (World, Bunkers, Free Zones, Special Categories, "... nes" areas); is_country separates them.
CREATE OR REPLACE TABLE silver.partners AS
SELECT
    CAST(PartnerCode AS INTEGER)        AS partner_code,
    PartnerDesc                         AS partner_name,
    NULLIF(PartnerCodeIsoAlpha3, '')    AS iso3,
    CAST(isGroup AS BOOLEAN)            AS is_group,
    NOT CAST(isGroup AS BOOLEAN)
        AND CAST(PartnerCode AS INTEGER) NOT IN (837, 838, 839, 899)
        AND PartnerDesc NOT LIKE '%, nes' AS is_country
FROM bronze.ref_partners
QUALIFY row_number() OVER (PARTITION BY PartnerCode ORDER BY entryEffectiveDate DESC) = 1;

CREATE OR REPLACE TABLE silver.reporters AS
SELECT
    CAST(reporterCode AS INTEGER)       AS reporter_code,
    reporterDesc                        AS reporter_name,
    NULLIF(reporterCodeIsoAlpha3, '')   AS iso3,
    CAST(isGroup AS BOOLEAN)            AS is_group
FROM bronze.ref_reporters
QUALIFY row_number() OVER (PARTITION BY reporterCode ORDER BY entryEffectiveDate DESC) = 1;

-- HS descriptions with the "NN - " code prefix stripped.
CREATE OR REPLACE TABLE silver.hs AS
SELECT
    hs_version,
    CAST(id AS VARCHAR)                        AS hs_code,
    CAST(aggrlevel AS INTEGER)                 AS hs_level,
    regexp_replace(text, '^\S+\s+-\s+', '')    AS description
FROM bronze.ref_hs
WHERE id <> 'TOTAL';
