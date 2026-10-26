# NSW electricity demand: a data quality audit

An audit of two public Australian time series — NSW electricity demand from AEMO
and Sydney temperature from Open-Meteo — to establish what they can and cannot
support before anyone builds a model on them.

**Status:** toolkit complete and self-tested. Analysis of the real data and the
write-up are in progress.

## Why

Electricity demand in NSW rises on hot days and on cold days, and falls in
between. It is one of the clearest non-linear relationships in any public
Australian dataset, and it is lagged — a run of hot nights matters more than a
single hot afternoon.

That makes it an obvious thing to model. This project does the step that usually
gets skipped: checking whether the data is sound enough to model at all.

## What the audit checks

| Check | The question | Why it matters |
|---|---|---|
| Gaps | Are time steps missing entirely? | A missing row and a row with a missing value are different things, and most code treats them differently without saying so |
| Duplicates | Is a timestamp repeated? | In Australian data this is often the April daylight saving rollback, where 2am happens twice |
| Missing values | Where are the nulls, and are they clustered? | Clustered nulls mean something broke for a period; scattered nulls mean something else |
| Outliers | Values far outside the usual range (3× IQR) | Some are sentinel codes standing in for "missing". Some are the most interesting real events in the data |
| Flatlines | Runs of identical values | A failed sensor often keeps reporting its last reading. That looks like data and isn't |
| Year-on-year stability | Does the series behave the same way throughout? | A jump in mean or variance between years usually means a definitional or instrument change, not a change in the world |

## Testing the checks themselves

A check that never fires looks exactly like clean data. So before running the
audit on anything real, `selftest.py` builds a synthetic series with six faults
planted in known places — one for each check — and confirms every one is caught.

```bash
python selftest.py
```

## Running it

```bash
pip install pandas requests
python selftest.py                                   # confirm the checks work
python get_weather.py 2015-01-01 2024-12-31          # Sydney daily temperature
python get_demand.py 2015-01 2024-12                 # NSW demand from AEMO
python audit.py data/weather_sydney.csv date
python audit.py data/demand_nsw.csv SETTLEMENTDATE
```

`get_demand.py` downloads one file per month, skips months already downloaded,
and combines them. Data is written to `data/`, which is not committed.

## Questions the audit is designed to test

- **Rooftop solar.** Behind-the-meter generation reduces *measured* demand without
  reducing electricity use. Has its growth made demand non-comparable across the
  decade? The year-on-year stability check is aimed at this.
- **Grid cell versus station.** Open-Meteo returns modelled values for a grid
  cell, not a weather station reading. `get_weather.py` prints the coordinates
  and elevation actually used, which matters for a coastal city.

## Files

| File | Purpose |
|---|---|
| `audit.py` | The six checks, run against any time series CSV |
| `selftest.py` | Synthetic data with planted faults, to confirm each check works |
| `get_weather.py` | Downloads daily Sydney temperature from the Open-Meteo archive |
| `get_demand.py` | Downloads and combines monthly NSW demand files from AEMO |

## Data sources

- Temperature: [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api)
- Demand: [AEMO aggregated price and demand data](https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/aggregated-data)

## Acknowledgement

Initial toolkit written with assistance from Claude (Anthropic).
