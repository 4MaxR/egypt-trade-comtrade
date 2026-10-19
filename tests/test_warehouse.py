"""Data-quality checks on the built warehouse. Run after scripts/build_warehouse.py."""

import json

import pytest

from egypt_trade.comtrade import PREVIEW_ROW_CAP
from egypt_trade.config import JOBS, RAW_DIR, WAREHOUSE, YEARS
from egypt_trade.warehouse import connect

pytestmark = pytest.mark.skipif(not WAREHOUSE.exists(), reason="warehouse not built")


@pytest.fixture(scope="module")
def con():
    with connect(read_only=True) as c:
        yield c


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def test_every_job_has_every_year():
    for job in JOBS:
        assert sorted(int(p.stem) for p in (RAW_DIR / job.name).glob("*.json")) == YEARS


def test_no_response_hit_the_preview_row_cap():
    for path in RAW_DIR.glob("*/*.json"):
        assert len(json.loads(path.read_text(encoding="utf-8"))) < PREVIEW_ROW_CAP, path


def test_silver_trade_has_unique_keys(con):
    dupes = scalar(
        con,
        """
        SELECT count(*) FROM (
            SELECT 1 FROM silver.trade
            GROUP BY source_job, year, reporter_code, partner_code, flow, cmd_code
            HAVING count(*) > 1)
    """,
    )
    assert dupes == 0


def test_world_totals_cover_every_year_and_flow(con):
    assert scalar(con, "SELECT count(*) FROM gold.fact_egypt_world") == len(YEARS) * 2


@pytest.mark.parametrize("table", ["gold.fact_egypt_partner", "gold.fact_egypt_hs2"])
def test_detail_tables_reconcile_to_world_totals(con, table):
    worst = scalar(
        con,
        f"""
        SELECT max(abs(d.total / w.value_usd - 1))
        FROM (SELECT year, flow, sum(value_usd) AS total FROM {table} GROUP BY ALL) AS d
        JOIN gold.fact_egypt_world AS w USING (year, flow)
    """,
    )
    assert worst < 0.001


def test_every_partner_code_is_in_the_dimension(con):
    orphans = scalar(
        con,
        """
        SELECT count(*) FROM gold.fact_egypt_partner
        ANTI JOIN gold.dim_partner USING (partner_code)
    """,
    )
    assert orphans == 0


def test_values_are_positive(con):
    assert scalar(con, "SELECT count(*) FROM silver.trade WHERE value_usd < 0") == 0
