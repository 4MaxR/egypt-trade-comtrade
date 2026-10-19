"""Project-wide constants: paths, the study window and the extraction jobs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
REF_DIR = ROOT / "data" / "reference"
WAREHOUSE = ROOT / "data" / "egypt_trade.duckdb"
SQL_DIR = ROOT / "sql"
CHART_DIR = ROOT / "outputs" / "charts"
TABLE_DIR = ROOT / "outputs" / "tables"

EGYPT = 818
WORLD = 0
YEARS = list(range(2014, 2026))

# HS4 headings followed in detail: Egypt is the world's largest wheat buyer, and natural
# gas flipped from export earner to import bill inside this window.
STRATEGIC_HS4 = {
    "1001": "Wheat and meslin",
    "1005": "Maize (corn)",
    "1507": "Soybean oil",
    "2709": "Crude petroleum",
    "2710": "Refined petroleum products",
    "2711": "Petroleum gases (LNG / natural gas)",
    "3102": "Nitrogen fertilisers",
}


@dataclass(frozen=True)
class Job:
    """One Comtrade query, run once per year. `params` excludes `period`."""

    name: str
    description: str
    params: dict[str, str]


JOBS = [
    Job(
        "egypt_by_partner",
        "Egypt-reported imports and exports, all commodities, by partner (incl. World)",
        {"reporterCode": str(EGYPT), "flowCode": "M,X", "cmdCode": "TOTAL"},
    ),
    Job(
        "egypt_by_hs2",
        "Egypt-reported imports and exports with the World, by HS chapter",
        {
            "reporterCode": str(EGYPT),
            "partnerCode": str(WORLD),
            "flowCode": "M,X",
            "cmdCode": "AG2",
        },
    ),
    Job(
        "egypt_strategic_hs4",
        "Egypt-reported trade in strategic HS4 headings, by partner",
        {"reporterCode": str(EGYPT), "flowCode": "M,X", "cmdCode": ",".join(STRATEGIC_HS4)},
    ),
    Job(
        "mirror_partners",
        "What every other country reports trading with Egypt (mirror data)",
        {"partnerCode": str(EGYPT), "flowCode": "M,X", "cmdCode": "TOTAL"},
    ),
]
