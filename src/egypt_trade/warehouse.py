"""Build the DuckDB warehouse from data/raw and run the analysis queries."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from .config import RAW_DIR, REF_DIR, SQL_DIR, WAREHOUSE

LAYERS = ["bronze", "silver", "gold"]


def _render(sql_file: Path) -> str:
    return sql_file.read_text(encoding="utf-8").format(
        raw_dir=RAW_DIR.as_posix(), ref_dir=REF_DIR.as_posix()
    )


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(WAREHOUSE), read_only=read_only)


def build() -> None:
    """Run every bronze, silver and gold script in file-name order."""
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        for layer in LAYERS:
            for sql_file in sorted((SQL_DIR / layer).glob("*.sql")):
                con.execute(_render(sql_file))
                print(f"built  {layer}/{sql_file.name}")
        for schema, table, rows in con.execute(
            """
            SELECT schema_name, table_name, estimated_size
            FROM duckdb_tables() WHERE schema_name IN ('silver', 'gold')
            ORDER BY schema_name, table_name
            """
        ).fetchall():
            print(f"  {schema}.{table:<24} {rows:>7,} rows")


def analysis_queries() -> list[Path]:
    return sorted((SQL_DIR / "analysis").glob("*.sql"))


def query(sql_or_file: str | Path, con: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    sql = (
        Path(sql_or_file).read_text(encoding="utf-8")
        if isinstance(sql_or_file, Path)
        else sql_or_file
    )
    if con is not None:
        return con.execute(sql).df()
    with connect(read_only=True) as own:
        return own.execute(sql).df()
