"""Step 3: run sql/analysis queries; save CSVs to outputs/tables, figures to outputs/charts."""

from egypt_trade import charts
from egypt_trade.config import CHART_DIR, TABLE_DIR
from egypt_trade.warehouse import analysis_queries, connect, query

TABLE_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

results = {}
with connect(read_only=True) as con:
    for sql_file in analysis_queries():
        df = query(sql_file, con)
        df.to_csv(TABLE_DIR / f"{sql_file.stem}.csv", index=False)
        results[sql_file.stem] = df
        print(f"{sql_file.stem:<28} {len(df):>4} rows")

charts.trade_balance(results["01_trade_balance"], CHART_DIR / "trade_balance.png")
charts.import_partners(results["02_top_partners"], CHART_DIR / "import_partners.png")
charts.wheat_sourcing(results["05_wheat_sourcing"], CHART_DIR / "wheat_sourcing.png")
charts.gas_swing(results["06_energy_swing"], CHART_DIR / "gas_swing.png")
charts.mirror_ratio(results["08_mirror_by_year"], CHART_DIR / "mirror_ratio.png")
print(f"charts -> {CHART_DIR}")
