"""
Download NSW electricity demand from AEMO's aggregated price and demand data.

AEMO publishes one CSV per region per month. Downloading ten years by hand
is 120 files; this does it for you, skips months you already have, and
combines everything into one file.

Writes data/raw/*.csv (one per month) and data/demand_nsw.csv (combined).

Usage:
    python get_demand.py 2015-01 2024-12
    python get_demand.py 2015-01 2024-12 VIC1     # other regions work too
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

URL = "https://aemo.com.au/aemo/data/nem/priceanddemand/PRICE_AND_DEMAND_{ym}_{region}.csv"

# AEMO rejects requests that don't look like they come from a browser.
HEADERS = {"User-Agent": "Mozilla/5.0 (data-quality-audit; educational project)"}


def months(start: str, end: str) -> list[str]:
    """'2015-01', '2015-03' -> ['201501', '201502', '201503']"""
    return [p.strftime("%Y%m") for p in pd.period_range(start, end, freq="M")]


def fetch_month(ym: str, region: str, raw_dir: Path) -> Path | None:
    out = raw_dir / f"{region}_{ym}.csv"
    if out.exists() and out.stat().st_size > 0:
        return out  # already downloaded on a previous run

    url = URL.format(ym=ym, region=region)
    for attempt in (1, 2):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200 and r.content.strip():
                out.write_bytes(r.content)
                return out
            print(f"  {ym}: HTTP {r.status_code}")
        except requests.RequestException as e:
            print(f"  {ym}: {e}")
        if attempt == 1:
            time.sleep(3)
    return None


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    start, end = sys.argv[1], sys.argv[2]
    region = sys.argv[3] if len(sys.argv) > 3 else "NSW1"

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    wanted = months(start, end)
    print(f"Fetching {len(wanted)} months of {region} demand from AEMO...")

    got, failed = [], []
    for ym in wanted:
        path = fetch_month(ym, region, raw_dir)
        (got if path else failed).append(path or ym)
        time.sleep(0.5)  # be polite to AEMO's server

    if not got:
        print("Nothing downloaded. Check your internet connection.")
        sys.exit(1)

    # Combine. Deliberately no cleaning, sorting fixes or deduplication here:
    # finding those problems is the audit's job, not the download's.
    combined = pd.concat((pd.read_csv(p) for p in got), ignore_index=True)
    out = Path(f"data/demand_{region[:-1].lower()}.csv")
    combined.to_csv(out, index=False)

    print(f"\nWrote {out} — {len(combined):,} rows from {len(got)} monthly files.")
    print(f"Columns: {list(combined.columns)}")
    if failed:
        print(f"\nFailed months ({len(failed)}): {', '.join(failed)}")
        print("Re-run the same command to retry just those — finished months are skipped.")


if __name__ == "__main__":
    main()
