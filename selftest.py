"""
Check that audit.py actually catches things, by giving it data with known faults.

Why this exists: a check that never fires looks the same as a clean dataset.
Before trusting the audit on real data, confirm each check finds the problem it
was written for.

This builds two years of plausible Sydney daily temperature, plants six faults
in known places, and runs the audit over it. Every fault below should appear in
the output. If one doesn't, that check is broken.

    python selftest.py

Planted faults:
    1. GAP        — 5 days removed in March 2016
    2. DUPLICATE  — 2016-04-03 appears twice (daylight saving rollback shape)
    3. MISSING    — 12 consecutive nulls in tmax, August 2015 (clustered)
    4. OUTLIER    — three -9999.0 sentinel values standing in for "missing"
    5. FLATLINE   — 9 identical tmin readings, a stuck sensor, June 2016
    6. INSTABILITY— 2016 tmax shifted +4C, as a instrument change would look
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("data/selftest_weather.csv")


def build() -> pd.DataFrame:
    rng = np.random.default_rng(20260101)
    dates = pd.date_range("2015-01-01", "2016-12-31", freq="D")

    # Sydney-ish seasonal cycle: warm Jan, cool Jul, peak around day 20.
    day_of_year = dates.dayofyear.to_numpy()
    seasonal = 22.5 + 5.5 * np.cos(2 * np.pi * (day_of_year - 20) / 365.25)

    tmax = seasonal + 3.5 + rng.normal(0, 2.5, len(dates))
    tmin = seasonal - 4.5 + rng.normal(0, 2.0, len(dates))

    df = pd.DataFrame({"date": dates, "tmax": tmax.round(1), "tmin": tmin.round(1)})

    # 6. INSTABILITY — every 2016 tmax reading 4 degrees warmer.
    df.loc[df["date"].dt.year == 2016, "tmax"] += 4.0

    # 3. MISSING — 12 clustered nulls in August 2015.
    df.loc[(df["date"] >= "2015-08-05") & (df["date"] <= "2015-08-16"), "tmax"] = np.nan

    # 4. OUTLIER — sentinel values pretending to be data.
    for d in ["2015-05-11", "2015-11-02", "2016-09-19"]:
        df.loc[df["date"] == d, "tmin"] = -9999.0

    # 5. FLATLINE — stuck sensor repeating one reading for 9 days.
    stuck = (df["date"] >= "2016-06-10") & (df["date"] <= "2016-06-18")
    df.loc[stuck, "tmin"] = 8.3

    # 2. DUPLICATE — 2016-04-03 recorded twice.
    dupe = df[df["date"] == "2016-04-03"].copy()
    df = pd.concat([df, dupe], ignore_index=True)

    # 1. GAP — five days in March 2016 never written at all.
    gap = (df["date"] >= "2016-03-07") & (df["date"] <= "2016-03-11")
    df = df[~gap]

    return df.sort_values("date").reset_index(drop=True)


def main() -> None:
    Path("data").mkdir(exist_ok=True)
    df = build()
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT} — {len(df)} rows with six planted faults.\n")
    print("=" * 62)

    subprocess.run([sys.executable, "audit.py", str(OUT), "date"], check=True)

    print("\n" + "=" * 62)
    print("""WHAT YOU SHOULD SEE ABOVE

  GAPS        one 6-day interval after 2016-03-06
  DUPLICATES  two rows dated 2016-04-03
  MISSING     12 nulls in tmax, all of them in 2015
  OUTLIERS    tmin minimum of -9999.00, three values beyond 3x IQR
  FLATLINES   a run of 9 identical tmin values of 8.3
  STABILITY   2016 tmax mean roughly 4 degrees above 2015, and 2016
              showing ~361 rows against 2015's 365

If any of those is absent, that check does not work and you should not
trust it on the real data. If all six are there, the audit is sound and
the only thing left is what the findings mean.""")


if __name__ == "__main__":
    main()
