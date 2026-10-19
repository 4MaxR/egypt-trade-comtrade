-- Data quality: do the detail tables add back up to Egypt's World totals, and how much
-- value sits in non-country buckets (Bunkers, "Areas, nes", "Other Asia, nes", ...)?
WITH partner_sum AS (
    SELECT f.year, f.flow,
           sum(f.value_usd)                                    AS partner_total,
           sum(f.value_usd) FILTER (WHERE NOT p.is_country)    AS non_country_total
    FROM gold.fact_egypt_partner AS f
    JOIN gold.dim_partner AS p USING (partner_code)
    GROUP BY ALL
),
hs2_sum AS (
    SELECT year, flow, sum(value_usd) AS hs2_total, count(*) AS chapters
    FROM gold.fact_egypt_hs2
    GROUP BY ALL
)
SELECT
    w.year,
    w.flow,
    w.hs_version,
    w.value_usd                              AS world_total_usd,
    ps.partner_total / w.value_usd           AS partner_sum_ratio,
    hs.hs2_total / w.value_usd               AS hs2_sum_ratio,
    hs.chapters                              AS hs2_chapters,
    ps.non_country_total / w.value_usd       AS non_country_share
FROM gold.fact_egypt_world AS w
JOIN partner_sum AS ps USING (year, flow)
JOIN hs2_sum AS hs USING (year, flow)
ORDER BY w.flow, w.year;
