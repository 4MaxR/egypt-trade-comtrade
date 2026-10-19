"""Step 1: pull Egypt's trade from UN Comtrade into data/raw/.

uv run python scripts/extract.py            # only missing files
uv run python scripts/extract.py --force    # re-download everything
"""

import argparse

from egypt_trade.extract import extract

parser = argparse.ArgumentParser()
parser.add_argument("--force", action="store_true", help="re-download files that already exist")
extract(force=parser.parse_args().force)
