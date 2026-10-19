-- Bronze: API responses and reference lists loaded as-is. No filtering, no renaming.
-- {raw_dir} and {ref_dir} are filled in by egypt_trade.warehouse.

CREATE SCHEMA IF NOT EXISTS bronze;

CREATE OR REPLACE TABLE bronze.comtrade_records AS
SELECT *
FROM read_json(
    '{raw_dir}/*/*.json',
    format = 'array',
    union_by_name = true,
    sample_size = -1,
    filename = 'source_file'
);

CREATE OR REPLACE TABLE bronze.ref_partners AS
SELECT * FROM read_json('{ref_dir}/partners.json', format = 'array');

CREATE OR REPLACE TABLE bronze.ref_reporters AS
SELECT * FROM read_json('{ref_dir}/reporters.json', format = 'array');

CREATE OR REPLACE TABLE bronze.ref_hs AS
SELECT 'H6' AS hs_version, * FROM read_json('{ref_dir}/hs_h6.json', format = 'array', sample_size = -1)
UNION ALL BY NAME
SELECT 'H4' AS hs_version, * FROM read_json('{ref_dir}/hs_h4.json', format = 'array', sample_size = -1);
