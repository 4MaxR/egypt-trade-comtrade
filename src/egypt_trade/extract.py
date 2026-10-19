"""Download every job x year into data/raw as JSON files (the bronze source).

Files that already exist are skipped, so a failed run can simply be restarted.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from .comtrade import Client
from .config import JOBS, RAW_DIR, REF_DIR, YEARS

REFERENCES = {"partnerAreas": "partners", "Reporters": "reporters", "H6": "hs_h6", "H4": "hs_h4"}


def extract(years: list[int] = YEARS, force: bool = False, client: Client | None = None) -> None:
    client = client or Client()
    REF_DIR.mkdir(parents=True, exist_ok=True)
    for remote, local in REFERENCES.items():
        path = REF_DIR / f"{local}.json"
        if force or not path.exists():
            path.write_text(json.dumps(client.reference(remote)), encoding="utf-8")
            print(f"reference  {local:<22} saved")

    for job in JOBS:
        job_dir = RAW_DIR / job.name
        job_dir.mkdir(parents=True, exist_ok=True)
        for year in years:
            path = job_dir / f"{year}.json"
            if path.exists() and not force:
                continue
            rows = client.get(year, **job.params)
            stamp = datetime.now(UTC).isoformat(timespec="seconds")
            for row in rows:
                row["_job"] = job.name
                row["_extracted_at"] = stamp
            path.write_text(json.dumps(rows), encoding="utf-8")
            print(f"{job.name:<22} {year}  {len(rows):>4} rows")
