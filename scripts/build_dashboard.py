"""Step 4: export dashboard data from the warehouse and render docs/dashboard.html.

The template (scripts/dashboard_template.html) holds page content only. Two files are written:
  docs/dashboard.html           standalone page with its own <!doctype> (GitHub Pages)
  outputs/dashboard_body.html   the same page without the document wrapper (artifact publish)
"""

import json
from datetime import date

from egypt_trade.config import JOBS, RAW_DIR, ROOT, YEARS
from egypt_trade.warehouse import analysis_queries, connect, query

TEMPLATE = ROOT / "scripts" / "dashboard_template.html"
PAGE = ROOT / "docs" / "dashboard.html"
BODY = ROOT / "outputs" / "dashboard_body.html"

SHORT_PARTNER = {
    "Russian Federation": "Russia",
    "United Arab Emirates": "UAE",
    "Rep. of Korea": "South Korea",
    "United Kingdom": "UK",
}
SHORT_HS2 = {
    "07": "Vegetables",
    "08": "Fruit & nuts",
    "10": "Cereals",
    "25": "Salt, stone & cement",
    "27": "Mineral fuels & oils",
    "29": "Organic chemicals",
    "30": "Pharmaceuticals",
    "31": "Fertilisers",
    "39": "Plastics",
    "62": "Apparel (woven)",
    "71": "Gold, gems & precious metals",
    "72": "Iron & steel",
    "73": "Iron & steel articles",
    "84": "Machinery",
    "85": "Electrical equipment",
    "87": "Vehicles & parts",
}
ENERGY_NAMES = {
    "2711": "Natural gas & LNG",
    "2710": "Refined fuels",
    "2709": "Crude oil",
}


def short(name: str) -> str:
    return SHORT_PARTNER.get(name, name)


def records(df):
    return json.loads(df.to_json(orient="records"))


def main() -> None:
    q = {f.stem: query(f) for f in analysis_queries()}

    with connect(read_only=True) as con:
        partners = con.execute("""
            WITH ranked AS (
                SELECT flow, partner_code,
                       row_number() OVER (PARTITION BY flow ORDER BY sum(value_usd) DESC) AS rnk
                FROM gold.fact_egypt_partner JOIN gold.dim_partner USING (partner_code)
                WHERE is_country GROUP BY flow, partner_code
            )
            SELECT f.year, f.flow, r.rnk, p.partner_name, f.value_usd,
                   f.value_usd / w.value_usd AS share
            FROM gold.fact_egypt_partner f
            JOIN ranked r USING (flow, partner_code)
            JOIN gold.dim_partner p USING (partner_code)
            JOIN gold.fact_egypt_world w USING (year, flow)
            WHERE r.rnk <= 5
            ORDER BY f.flow, r.rnk, f.year
        """).df()
        counts = dict(
            con.execute("SELECT source_job, count(*) FROM silver.trade GROUP BY 1").fetchall()
        )
        gold_tables = con.execute(
            "SELECT count(*) FROM duckdb_tables() WHERE schema_name = 'gold'"
        ).fetchone()[0]
        dupes = con.execute("""
            SELECT count(*) FROM (SELECT 1 FROM silver.trade
            GROUP BY source_job, year, reporter_code, partner_code, flow, cmd_code
            HAVING count(*) > 1)
        """).fetchone()[0]
        extracted = con.execute("SELECT max(extracted_at)::DATE FROM silver.trade").fetchone()[0]
        partner_dim = con.execute("SELECT count(*) FROM gold.dim_partner").fetchone()[0]

    def partner_block(flow):
        df = partners[partners.flow == flow]
        out = []
        for name, g in df.groupby("partner_name", sort=False):
            g = g.set_index("year").reindex(YEARS)
            out.append(
                {
                    "name": short(name),
                    "share": [None if v != v else v for v in g["share"]],
                    "value": [None if v != v else v for v in g["value_usd"]],
                }
            )
        return out

    def mix_block(flow):
        df = q["04_product_mix"][q["04_product_mix"].flow == flow]
        out = []
        for hs2, g in df.groupby("hs2", sort=False):
            g = g.set_index("year").reindex(YEARS)
            desc = g["description"].dropna().iloc[0]
            out.append(
                {
                    "hs2": hs2,
                    "name": SHORT_HS2.get(hs2, desc.split(";")[0][:40]),
                    "full": desc,
                    "share": list(g["share_of_total"]),
                    "value": list(g["value_usd"]),
                }
            )
        return out

    energy = {}
    for hs4, g in q["06_energy_swing"].groupby("hs4"):
        g = g.set_index("year").reindex(YEARS)
        energy[hs4] = {
            "name": ENERGY_NAMES[hs4],
            "exports": list(g["exports_usd"].fillna(0)),
            "imports": list(g["imports_usd"].fillna(0)),
        }

    wheat_df = q["05_wheat_sourcing"].copy()
    main_origins = ["Russian Federation", "Ukraine", "Romania", "France"]
    wheat_df["origin"] = wheat_df["origin"].where(wheat_df["origin"].isin(main_origins), "Other")
    wheat_df = wheat_df.groupby(["year", "origin"], as_index=False)[["value_usd", "share"]].sum()
    wheat = []
    for origin in [*main_origins, "Other"]:
        g = wheat_df[wheat_df.origin == origin].set_index("year").reindex(YEARS).fillna(0)
        wheat.append(
            {"name": short(origin), "share": list(g["share"]), "value": list(g["value_usd"])}
        )

    mirror_year = {}
    for flow, g in q["08_mirror_by_year"].groupby("egypt_flow"):
        g = g.set_index("year").reindex(YEARS)
        mirror_year[flow] = {
            "ratio": list(g["egypt_to_partner_ratio"]),
            "egypt": list(g["egypt_reported_usd"]),
            "partner": list(g["partner_reported_usd"]),
            "partners": [int(v) for v in g["matched_partners"]],
        }

    outliers = q["07_mirror_gaps"].head(12).copy()
    outliers["partner_name"] = outliers["partner_name"].map(short)

    dq = q["09_data_quality"]
    raw_files = len(list(RAW_DIR.glob("*/*.json")))
    data = {
        "years": YEARS,
        "meta": {
            "built": date.today().isoformat(),
            "extracted": extracted.isoformat(),
            "raw_files": raw_files,
            "silver_rows": int(sum(counts.values())),
            "gold_tables": int(gold_tables),
            "partners": int(partner_dim),
            "jobs": [
                {"name": j.name, "description": j.description, "rows": int(counts.get(j.name, 0))}
                for j in JOBS
            ],
            "checks": {
                "partner_dev": float((dq["partner_sum_ratio"] - 1).abs().max()),
                "hs2_dev": float((dq["hs2_sum_ratio"] - 1).abs().max()),
                "duplicates": int(dupes),
                "years_complete": all(
                    len(list((RAW_DIR / j.name).glob("*.json"))) == len(YEARS) for j in JOBS
                ),
                "max_rows_per_call": max(
                    len(json.loads(p.read_text(encoding="utf-8")))
                    for p in RAW_DIR.glob("*/*.json")
                ),
            },
        },
        "balance": records(q["01_trade_balance"]),
        "partners": {"import": partner_block("import"), "export": partner_block("export")},
        "concentration": records(q["03_partner_concentration"]),
        "mix": {"import": mix_block("import"), "export": mix_block("export")},
        "energy": energy,
        "wheat": wheat,
        "mirror_year": mirror_year,
        "outliers": records(outliers),
        "quality": records(dq),
    }

    body = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(data, separators=(",", ":"))
    )
    BODY.parent.mkdir(parents=True, exist_ok=True)
    BODY.write_text(body, encoding="utf-8")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        "</head>\n<body>\n" + body + "\n</body>\n</html>\n",
        encoding="utf-8",
    )
    print(f"dashboard -> {PAGE.relative_to(ROOT)} ({PAGE.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
