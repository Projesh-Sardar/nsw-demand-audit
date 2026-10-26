"""
Pull daily Sydney temperature from the Open-Meteo historical archive.

No API key needed. Writes data/weather_sydney.csv

Usage:
    python get_weather.py 2015-01-01 2024-12-31
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

BASE = "https://archive-api.open-meteo.com/v1/archive"

# Sydney Observatory Hill, roughly. Change if you want a different site.
LAT, LON = -33.86, 151.21

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "precipitation_sum",
]


def fetch(start: str, end: str) -> pd.DataFrame:
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start,
        "end_date": end,
        "daily": ",".join(DAILY_VARS),
        "timezone": "Australia/Sydney",
    }
    r = requests.get(BASE, params=params, timeout=60)
    r.raise_for_status()
    payload = r.json()

    daily = payload["daily"]
    df = pd.DataFrame(daily)
    df = df.rename(columns={"time": "date"})
    df["date"] = pd.to_datetime(df["date"])

    # Keep the units the API reported — you will want these in the write-up.
    print("Units reported by the API:")
    for k, v in payload.get("daily_units", {}).items():
        print(f"  {k}: {v}")
    print(f"Grid cell actually used: lat {payload['latitude']}, lon {payload['longitude']}, "
          f"elevation {payload.get('elevation')} m")
    print("(Note how far this is from the coordinates you asked for. "
          "That gap belongs in your write-up.)")

    return df


def main() -> None:
    start = sys.argv[1] if len(sys.argv) > 1 else "2015-01-01"
    end = sys.argv[2] if len(sys.argv) > 2 else "2024-12-31"

    Path("data").mkdir(exist_ok=True)

    # Chunk by year. Not strictly required, but it means a failure part-way
    # through does not cost you the whole pull, and it makes rate limiting
    # obvious if you hit it.
    frames = []
    for year in range(int(start[:4]), int(end[:4]) + 1):
        y_start = max(f"{year}-01-01", start)
        y_end = min(f"{year}-12-31", end)
        print(f"Fetching {y_start} to {y_end}...")
        frames.append(fetch(y_start, y_end))
        time.sleep(1)

    out = pd.concat(frames, ignore_index=True).sort_values("date")
    out.to_csv("data/weather_sydney.csv", index=False)
    print(f"\nWrote data/weather_sydney.csv — {len(out)} rows, "
          f"{out['date'].min().date()} to {out['date'].max().date()}")


if __name__ == "__main__":
    main()
